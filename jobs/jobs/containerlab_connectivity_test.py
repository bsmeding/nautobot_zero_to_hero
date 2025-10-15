#!/usr/bin/env python3
"""Containerlab Connectivity Test Job.

This job tests network connectivity between containerlab nodes
using ping, traceroute, and other network diagnostic tools.
"""

import subprocess
import socket
from nautobot.apps.jobs import Job, ChoiceVar, IntegerVar, register_jobs

name = "LAB Setup"


class ContainerlabConnectivityTest(Job):
    """
    Test network connectivity between containerlab nodes.
    
    This job executes network diagnostic commands (ping, traceroute, etc.)
    to verify network connectivity to containerlab nodes from Nautobot.
    """

    class Meta:
        name = "Containerlab Connectivity Test"
        description = "Test connectivity to containerlab nodes (ping, traceroute, etc.)"
        has_sensitive_variables = False

    # Node IP mapping based on containerlab configuration
    NODE_IPS = {
        "clab-nautobot-lab-mgmt": "172.20.20.5",
        "clab-nautobot-lab-workstation1": "172.20.20.4",
        "clab-nautobot-lab-access1": "172.20.20.11",
        "clab-nautobot-lab-access2": "172.20.20.12",
        "clab-nautobot-lab-dist1": "172.20.20.13",
        "clab-nautobot-lab-rtr1": "172.20.20.14",
    }

    destination_node = ChoiceVar(
        label="Destination Node",
        description="The containerlab node to test connectivity to",
        choices=(
            ("clab-nautobot-lab-mgmt", "Management Server (172.20.20.5)"),
            ("clab-nautobot-lab-workstation1", "Workstation 1 (172.20.20.4)"),
            ("clab-nautobot-lab-access1", "Access Switch 1 (172.20.20.11)"),
            ("clab-nautobot-lab-access2", "Access Switch 2 (172.20.20.12)"),
            ("clab-nautobot-lab-dist1", "Distribution Switch 1 (172.20.20.13)"),
            ("clab-nautobot-lab-rtr1", "Router 1 (172.20.20.14)"),
        ),
        required=True,
        default="clab-nautobot-lab-workstation1",
    )

    ping_count = IntegerVar(
        label="Ping Count",
        description="Number of ping packets to send",
        default=5,
        required=False,
    )

    def run(self, destination_node, ping_count):
        """Main execution method."""
        self.logger.info("=" * 80)
        self.logger.info(f"Connectivity Test from Nautobot → {destination_node}")
        self.logger.info("=" * 80)

        # Get the destination IP address
        dest_ip = self.NODE_IPS.get(destination_node)
        if not dest_ip:
            self.logger.error(f"Could not determine IP address for {destination_node}")
            return f"Error: Unknown node {destination_node}"

        self.logger.info(f"Destination IP: {dest_ip}")
        self.logger.info("")

        # Run connectivity tests
        results = []
        
        # Test 1: Ping test (critical)
        results.append(self._run_ping_test(dest_ip, ping_count))
        
        # Test 2: TCP port test (informational only - SSH may not be running)
        self._run_tcp_test(dest_ip, 22, "SSH")
        # Don't add to results since SSH is optional
        
        # Test 3: DNS resolution test (informational only)
        self._run_dns_test(destination_node)
        # Don't add to results since DNS may not be configured

        # Summary
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("Test Summary")
        self.logger.info("=" * 80)
        
        success_count = sum(1 for r in results if r)
        total_tests = len(results)
        
        self.logger.info(f"Critical tests passed: {success_count}/{total_tests}")
        self.logger.info("Note: SSH and DNS tests are informational only")
        
        if success_count == total_tests:
            self.logger.success("✓ All critical connectivity tests PASSED")
            return "Connectivity test passed - Node is reachable"
        else:
            self.logger.error(f"✗ Critical test(s) failed ({total_tests - success_count} failure(s))")
            return f"Connectivity test FAILED - Node may not be reachable"

    def _run_ping_test(self, dest_ip, count):
        """Run ping test to destination."""
        self.logger.info("-" * 80)
        self.logger.info(f"TEST 1: Ping Test ({count} packets)")
        self.logger.info("-" * 80)
        
        try:
            # Run ping command from Nautobot container
            cmd = ["ping", "-c", str(count), "-W", "2", dest_ip]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(result.stdout)
                # Parse ping statistics
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'packets transmitted' in line or 'min/avg/max' in line:
                        self.logger.info(f"  {line.strip()}")
                self.logger.success("✓ Ping test PASSED")
                return True
            else:
                self.logger.warning("Ping failed:")
                self.logger.warning(result.stdout)
                if result.stderr:
                    self.logger.warning(result.stderr)
                self.logger.error("✗ Ping test FAILED")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("✗ Ping test TIMEOUT")
            return False
        except Exception as e:
            self.logger.error(f"✗ Ping test EXCEPTION: {e}")
            return False

    def _run_tcp_test(self, dest_ip, port, service_name):
        """Test TCP connectivity to a specific port (informational only)."""
        self.logger.info("")
        self.logger.info("-" * 80)
        self.logger.info(f"TEST 2: TCP Port Test - {service_name} on port {port} (Informational)")
        self.logger.info("-" * 80)
        
        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            
            self.logger.info(f"Attempting to connect to {dest_ip}:{port}...")
            result = sock.connect_ex((dest_ip, port))
            sock.close()
            
            if result == 0:
                self.logger.info(f"✓ Port {port} is OPEN and accepting connections")
                self.logger.success(f"✓ {service_name} is accessible")
                return True
            else:
                self.logger.info(f"ℹ Port {port} is not accessible (error code: {result})")
                self.logger.info(f"  This is normal if {service_name} is not configured or running")
                return False
                
        except socket.timeout:
            self.logger.info(f"ℹ Connection to {dest_ip}:{port} timed out")
            self.logger.info(f"  This is normal if {service_name} is not running")
            return False
        except Exception as e:
            self.logger.info(f"ℹ TCP test could not complete: {e}")
            return False

    def _run_dns_test(self, hostname):
        """Test DNS resolution for the hostname (informational only)."""
        self.logger.info("")
        self.logger.info("-" * 80)
        self.logger.info("TEST 3: DNS Resolution Test (Informational)")
        self.logger.info("-" * 80)
        
        try:
            self.logger.info(f"Attempting to resolve hostname: {hostname}")
            
            # Try to resolve the hostname
            result = socket.gethostbyname(hostname)
            
            self.logger.info(f"✓ Hostname '{hostname}' resolved to: {result}")
            self.logger.success("✓ DNS resolution successful")
            return True
                
        except socket.gaierror as e:
            self.logger.info(f"ℹ DNS resolution failed: {e}")
            self.logger.info("  This is normal if containerlab DNS is not configured")
            return True
        except Exception as e:
            self.logger.info(f"ℹ DNS test could not complete: {e}")
            return True


register_jobs(ContainerlabConnectivityTest)

