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
        """Main execution method."""
        self.logger.info("=" * 80)
        self.logger.info(f"Connectivity Test: {source_vm.name} → {destination_vm.name}")
        self.logger.info("=" * 80)

        # Validate source and destination are different
        if source_vm.id == destination_vm.id:
            self.logger.error("Source and destination must be different!")
            return "Error: Cannot test connectivity to same VM"

        # Get IP addresses from VMs (using eth1 interface for data plane)
        source_ip = self._get_vm_data_plane_ip(source_vm)
        dest_ip = self._get_vm_data_plane_ip(destination_vm)
        
        if not source_ip:
            self.logger.error(f"Could not find data plane IP (eth1) for source VM: {source_vm.name}")
            return f"Error: {source_vm.name} has no eth1 IP address"
        
        if not dest_ip:
            self.logger.error(f"Could not find data plane IP (eth1) for destination VM: {destination_vm.name}")
            return f"Error: {destination_vm.name} has no eth1 IP address"

        self.logger.info(f"Source: {source_vm.name} ({source_ip})")
        self.logger.info(f"Destination: {destination_vm.name} ({dest_ip})")
        self.logger.info("")

        # Get source VM's management IP for SSH access
        source_mgmt_ip = self._get_vm_mgmt_ip(source_vm)
        if not source_mgmt_ip:
            self.logger.error(f"Could not find management IP for source VM: {source_vm.name}")
            return f"Error: {source_vm.name} has no management IP (primary_ip4)"

        # Run connectivity tests from source to destination
        results = []
        
        # Test 1: Ping test (critical) - SSH to source and ping from there
        results.append(self._run_ping_test_via_ssh(
            source_vm.name, 
            source_mgmt_ip, 
            dest_ip, 
            ping_count
        ))

        # Summary
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("Test Summary")
        self.logger.info("=" * 80)
        
        success_count = sum(1 for r in results if r)
        total_tests = len(results)
        
        self.logger.info(f"Critical tests passed: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            self.logger.success("✓ Connectivity test PASSED")
            return f"SUCCESS: Can reach {destination_vm.name} at {dest_ip}"
        else:
            self.logger.error(f"✗ Connectivity test FAILED")
            return f"FAILED: Cannot reach {destination_vm.name} at {dest_ip}"

    def _get_vm_data_plane_ip(self, vm):
        """Get the data plane IP address (eth1) for a VM.
        
        Args:
            vm: VirtualMachine object
            
        Returns:
            IP address string or None
        """
        from nautobot.virtualization.models import VMInterface
        
        try:
            # Get eth1 interface (data plane)
            eth1 = VMInterface.objects.get(virtual_machine=vm, name="eth1")
            
            # Get IP addresses assigned to this interface
            ip_addresses = eth1.ip_addresses.all()
            
            if ip_addresses:
                # Return first IP address without subnet mask
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
        
        Args:
            vm: VirtualMachine object
            
        Returns:
            IP address string or None
        """
        if vm.primary_ip4:
            return str(vm.primary_ip4.address).split('/')[0]
        elif vm.primary_ip:
            return str(vm.primary_ip.address).split('/')[0]
        return None

    def _run_ping_test_via_ssh(self, vm_name, mgmt_ip, dest_ip, count):
        """Run ping test via SSH to source VM.
        
        Args:
            vm_name: Name of source VM
            mgmt_ip: Management IP to SSH to
            dest_ip: Destination IP to ping
            count: Number of ping packets
            
        Returns:
            True if ping succeeds, False otherwise
        """
        self.logger.info("-" * 80)
        self.logger.info(f"TEST: Ping from {vm_name} to {dest_ip}")
        self.logger.info(f"      SSH to {mgmt_ip}, then ping {dest_ip} ({count} packets)")
        self.logger.info("-" * 80)
        
        if not PARAMIKO_AVAILABLE:
            self.logger.error("✗ paramiko library not available")
            self.logger.error("  Install with: pip install paramiko")
            return False
        
        try:
            # SSH credentials for containerlab VMs
            ssh_user = "root"
            ssh_pass = "admin"
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.logger.info(f"Connecting to {vm_name} at {mgmt_ip}...")
            ssh.connect(
                mgmt_ip,
                username=ssh_user,
                password=ssh_pass,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Run ping command
            ping_cmd = f"ping -c {count} -W 2 {dest_ip}"
            self.logger.info(f"Executing: {ping_cmd}")
            
            stdin, stdout, stderr = ssh.exec_command(ping_cmd)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            ssh.close()
            
            if exit_code == 0:
                self.logger.info("Ping output:")
                for line in output.splitlines():
                    self.logger.info(f"  {line}")
                self.logger.success("✓ Ping test PASSED")
                return True
            else:
                self.logger.warning("Ping failed:")
                for line in output.splitlines():
                    self.logger.warning(f"  {line}")
                if error:
                    self.logger.warning(f"Error: {error}")
                self.logger.error("✗ Ping test FAILED")
                return False
                
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

