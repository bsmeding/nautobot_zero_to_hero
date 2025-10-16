#!/usr/bin/env python3
"""Containerlab Connectivity Test Job.

This job tests network connectivity between containerlab nodes
using ping, traceroute, and other network diagnostic tools.
"""

import subprocess
import socket
from nautobot.apps.jobs import Job, ObjectVar, IntegerVar, register_jobs
from nautobot.virtualization.models import VirtualMachine

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

name = "LAB Setup"


class ContainerlabConnectivityTest(Job):
    """
    Test network connectivity between containerlab nodes.
    
    This job executes network diagnostic commands (ping, traceroute, etc.)
    to verify network connectivity to containerlab nodes from Nautobot.
    """

    class Meta:
        name = "Containerlab Connectivity Test"
        description = "Test data plane connectivity to containerlab nodes (tests 10.0.0.x IPs through switches)"
        has_sensitive_variables = False

    source_vm = ObjectVar(
        model=VirtualMachine,
        label="Source VM",
        description="Virtual machine to run tests FROM",
        required=True,
    )

    destination_vm = ObjectVar(
        model=VirtualMachine,
        label="Destination VM",
        description="Virtual machine to test connectivity TO",
        required=True,
    )

    ping_count = IntegerVar(
        label="Ping Count",
        description="Number of ping packets to send",
        default=5,
        required=False,
    )

    def run(self, source_vm, destination_vm, ping_count):
        """Main execution method - orchestrates the connectivity test between VMs."""
        # Print test header with source and destination VM names
        self.logger.info("=" * 80)
        self.logger.info(f"Connectivity Test: {source_vm.name} → {destination_vm.name}")
        self.logger.info("=" * 80)

        # Prevent testing a VM against itself
        if source_vm.id == destination_vm.id:
            self.logger.error("Source and destination must be different!")
            return "Error: Cannot test connectivity to same VM"

        # Retrieve data plane IPs from eth1 interfaces in Nautobot
        source_ip = self._get_vm_data_plane_ip(source_vm)
        dest_ip = self._get_vm_data_plane_ip(destination_vm)
        
        # Verify source VM has a data plane IP configured
        if not source_ip:
            self.logger.error(f"Could not find data plane IP (eth1) for source VM: {source_vm.name}")
            return f"Error: {source_vm.name} has no eth1 IP address"
        
        # Verify destination VM has a data plane IP configured
        if not dest_ip:
            self.logger.error(f"Could not find data plane IP (eth1) for destination VM: {destination_vm.name}")
            return f"Error: {destination_vm.name} has no eth1 IP address"

        # Display the VMs and their data plane IPs being tested
        self.logger.info(f"Source: {source_vm.name} ({source_ip})")
        self.logger.info(f"Destination: {destination_vm.name} ({dest_ip})")
        self.logger.info("")

        # Get management IP to SSH into the source VM
        source_mgmt_ip = self._get_vm_mgmt_ip(source_vm)
        if not source_mgmt_ip:
            self.logger.error(f"Could not find management IP for source VM: {source_vm.name}")
            return f"Error: {source_vm.name} has no management IP (primary_ip4)"

        # Execute connectivity tests and collect results
        results = []
        
        # Run ping test via SSH (tests actual network path through switches)
        results.append(self._run_ping_test_via_ssh(
            source_vm.name, 
            source_mgmt_ip, 
            dest_ip, 
            ping_count
        ))

        # Display test summary and results
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("Test Summary")
        self.logger.info("=" * 80)
        
        # Calculate pass/fail statistics
        success_count = sum(1 for r in results if r)
        total_tests = len(results)
        
        self.logger.info(f"Critical tests passed: {success_count}/{total_tests}")
        
        # Return final test result
        if success_count == total_tests:
            self.logger.success("✓ Connectivity test PASSED")
            return f"SUCCESS: Can reach {destination_vm.name} at {dest_ip}"
        else:
            self.logger.error(f"✗ Connectivity test FAILED")
            return f"FAILED: Cannot reach {destination_vm.name} at {dest_ip}"

    def _get_vm_data_plane_ip(self, vm):
        """Get the data plane IP address (eth1) for a VM.
        
        The data plane network (10.0.0.x) goes through the switches,
        allowing us to test actual network connectivity end-to-end.
        
        Args:
            vm: VirtualMachine object from Nautobot
            
        Returns:
            IP address string (without /24 suffix) or None if not found
        """
        from nautobot.virtualization.models import VMInterface
        
        try:
            # Query Nautobot for the VM's eth1 interface
            eth1 = VMInterface.objects.get(virtual_machine=vm, name="eth1")
            
            # Retrieve all IP addresses assigned to eth1
            ip_addresses = eth1.ip_addresses.all()
            
            if ip_addresses:
                # Extract IP address without CIDR notation (e.g., "10.0.0.15" from "10.0.0.15/24")
                ip_addr = str(ip_addresses[0].address).split('/')[0]
                return ip_addr
            else:
                self.logger.warning(f"VM {vm.name} eth1 has no IP addresses assigned")
                return None
                
        except VMInterface.DoesNotExist:
            self.logger.warning(f"VM {vm.name} has no eth1 interface")
            return None

    def _get_vm_mgmt_ip(self, vm):
        """Get the management IP address for a VM.
        
        Management IPs (172.20.20.x) are used to SSH into VMs.
        These are on the containerlab management network, not the data plane.
        
        Args:
            vm: VirtualMachine object from Nautobot
            
        Returns:
            IP address string (without /24 suffix) or None if not found
        """
        # Try IPv4 primary IP first
        if vm.primary_ip4:
            return str(vm.primary_ip4.address).split('/')[0]
        # Fall back to generic primary IP (could be IPv6)
        elif vm.primary_ip:
            return str(vm.primary_ip.address).split('/')[0]
        return None

    def _run_ping_test_via_ssh(self, vm_name, mgmt_ip, dest_ip, count):
        """Run ping test via SSH to source VM.
        
        This method:
        1. SSHs to the source VM using its management IP (172.20.20.x)
        2. Executes ping from the VM to the destination's data plane IP (10.0.0.x)
        3. Tests the actual network path through the switches
        
        Args:
            vm_name: Name of source VM (for logging)
            mgmt_ip: Management IP to SSH to (172.20.20.x)
            dest_ip: Destination data plane IP to ping (10.0.0.x)
            count: Number of ping packets to send
            
        Returns:
            True if ping succeeds (100% packets received), False otherwise
        """
        # Display test header
        self.logger.info("-" * 80)
        self.logger.info(f"TEST: Ping from {vm_name} to {dest_ip}")
        self.logger.info(f"      SSH to {mgmt_ip}, then ping {dest_ip} ({count} packets)")
        self.logger.info("-" * 80)
        
        # Check if paramiko library is available
        if not PARAMIKO_AVAILABLE:
            self.logger.error("✗ paramiko library not available")
            self.logger.error("  Install with: pip install paramiko")
            return False
        
        try:
            # Use default containerlab VM credentials
            ssh_user = "root"
            ssh_pass = "admin"
            
            # Initialize SSH client and accept unknown host keys
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Establish SSH connection to source VM
            self.logger.info(f"Connecting to {vm_name} at {mgmt_ip}...")
            ssh.connect(
                mgmt_ip,
                username=ssh_user,
                password=ssh_pass,
                timeout=10,
                look_for_keys=False,  # Don't try SSH key authentication
                allow_agent=False      # Don't use SSH agent
            )
            
            # Execute ping command on the source VM
            ping_cmd = f"ping -c {count} -W 2 {dest_ip}"
            self.logger.info(f"Executing: {ping_cmd}")
            
            stdin, stdout, stderr = ssh.exec_command(ping_cmd)
            exit_code = stdout.channel.recv_exit_status()  # Wait for command to complete
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            # Clean up SSH connection
            ssh.close()
            
            # Parse ping results and determine success/failure
            if exit_code == 0:
                # Ping succeeded - display output
                self.logger.info("Ping output:")
                for line in output.splitlines():
                    self.logger.info(f"  {line}")
                self.logger.success("✓ Ping test PASSED")
                return True
            else:
                # Ping failed - display failure details
                self.logger.warning("Ping failed:")
                for line in output.splitlines():
                    self.logger.warning(f"  {line}")
                if error:
                    self.logger.warning(f"Error: {error}")
                self.logger.error("✗ Ping test FAILED")
                return False
                
        # Handle various SSH and network errors
        except paramiko.AuthenticationException:
            self.logger.error(f"✗ SSH authentication failed to {mgmt_ip}")
            return False
        except paramiko.SSHException as e:
            self.logger.error(f"✗ SSH error: {e}")
            return False
        except socket.timeout:
            self.logger.error(f"✗ Connection timeout to {mgmt_ip}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Test exception: {e}")
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
            self.logger.info("  Note: This is the containerlab management IP")
            self.logger.info("  Data plane connectivity is tested using different IPs (10.0.0.x)")
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

