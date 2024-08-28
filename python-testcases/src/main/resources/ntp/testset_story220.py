"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2014
@author:    etomgly
@summary:   Tests for NTP plugin. Stories:
LITPCDS-220
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from litp_cli_utils import CLIUtils
import test_constants
import time


class Story220(GenericTest):
    """
    LITPCDS-220:
    As an Installer I want the NTP configured on the MS
    and Peer Nodes, so that time is always synchronized between all servers
    """

    def setUp(self):
        """
        Description:
        Runs before every single test
        Actions:
        1. Call the super class setup method
        2. Set up variables used in the tests
        Results:
        The super class prints out diagnostics and variables
        common to all tests are available.
        """
        # 1. Call super class setup
        super(Story220, self).setUp()
        self.redhat = RHCmdUtils()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.ntp_stat_cmd = "/usr/bin/ntpstat"
        self.timeout_mins = 3
        self.cli = CLIUtils()
        self.grep_file = "/etc/ntp.conf"
        self.ms_ip_address = self.get_node_att(self.ms_node, 'ipv4')

    def tearDown(self):
        """
        Description:
        Runs after every single test
        Actions:
        1. Perform Test Cleanup
        2. Call superclass teardown
        Results:
        Items used in the test are cleaned up
        and links removed
        """
        super(Story220, self).tearDown()

    def ntp_syncs_with_server(self, server, item_to_grep, server_name):
        """
        Description:
        This method takes in the server and the server name
        Actions:
        1. Create server(takes arg's of server hostname & item to grep
        and the server name)
        2. Create and run the plan
        3. Grep for argument that was passed in
        """

        # Step:1 create the ntp server item
        ntp_server = self.find(self.ms_node, "/software",
                        "ntp-server", False)[0]
        ntp_server_url = ntp_server + server_name
        self.execute_cli_create_cmd(
            self.ms_node, ntp_server_url, "ntp-server", server,
            add_to_cleanup=False)

        # Step 2: Create and run the plan
        # create the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # set a timeout
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        # Wait for plan to complete with success
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, self.timeout_mins)
        # ensure plan was successful
        self.assertTrue(completed_successfully, "Plan was not successful")

        # Step 3: Check the /etc/ntp.conf for the server
        # execute grep command
        cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, item_to_grep)
        std_out, std_err, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, exit_code)

        server_found = False

        # Look through all grep lines returned
        for line in std_out:
            line_start = line.split(item_to_grep)[0]
            if "#" not in line_start:
                server_found = True
                break

        self.assertTrue(server_found)

        # Step 4: run ntpstat on the ms to ensure ntp re-syncs
        self.wait_for_cmd(self.ms_node, self.ntp_stat_cmd, 0, timeout_mins=5)

    @attr('all', 'non-revert', 'cdb_priority1')
    def test_01_p_ntp_in_sync(self):
        """
        @tms_id: litpcds_220_tc01
        @tms_requirements_id: LITPCDS-220
        @tms_title: Ensure ntp is syncing system wide, check that local clock
        and stratum are uncommented in ms ntp.conf
        @tms_description: This method ensures that the ntp service is in sync
        and checks the ntp.conf for uncommented local clock and stratum values
        @tms_test_steps:
            @step:  Run ntpstat on the ms to ensure ntp is in sync
            @result:Ntp is in sync
            @step:  Check each node's ntp.conf file for the ms ip
            @result:Each node's ntp.conf file contains the ms ip
            @step:  Check both nodes are in sync with the ms by running ntpstat
            @result:Nodes are in sync with the ms
            @step:  Check the ntp.conf for the uncommented local clock and
            stratum lines
            @result:Local clock and stratum lines is present and uncommented.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # Step 1: run ntpstat on the ms
        self.assertTrue(self.wait_for_cmd(self.ms_node, self.ntp_stat_cmd, 0,
                                          timeout_mins=20))
        # Step 2: loop through the nodes
        for node in self.mn_nodes:
            # Step 3: check that the ms ip is in the /etc/ntp.conf of each node
            grep_for = "server " + self.ms_ip_address
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, grep_for)
            std_out, std_err, exit_code = self.run_command(node, cmd)
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)
            # Step 4: run the ntpstat command on each node
            self.assertTrue(self.wait_for_cmd(node, self.ntp_stat_cmd, 0,
                                              timeout_mins=40))
        # Step 5: check ntp.conf file for uncommented local clock and stratum
        # lines
        lines = ["^server.127.127.1.0.# local clock",
                 "^fudge.127.127.1.0.stratum 10"]
        for grep_for in lines:
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file,
                                                 grep_for, "-E")
            std_out, std_err, exit_code = self.run_command(self.ms_node, cmd)
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)

    @attr('all', 'non-revert')
    def test_02_p_ntp_syncs_loopback(self):
        """
        @tms_id: litpcds_220_tc02
        @tms_requirements_id: LITPCDS-220
        @tms_title: Ensure ntp is syncing with server loopback address
        @tms_description: This method ensures that the ntp service is in sync
            with the server loopback address once set
        @tms_test_steps:
            @step: 1 Create the ntp server item
            @result: Ntp server item created
            @step: 2 Create and run the plan
            @result: Plan created and run successfully
            @step: 3 Check the /etc/ntp.conf for the server
            @result: /etc/ntp.conf contains the server
            @step: 4 run ntpstat on the ms to ensure ntp re-syncs
            @result: Ntp service is synced to the server loopback address
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # Step 1: Call the ntp sync method
        self.ntp_syncs_with_server(
            server="server='127.127.1.0'",
            item_to_grep=r"server 127.127.1.0",
            server_name="/server_220_a")

    @attr('all', 'non-revert')
    def test_03_p_syncs_to_external(self):
        """
        @tms_id: litpcds_220_tc03
        @tms_requirements_id: LITPCDS-220
        @tms_title: ntp updates server
        @tms_description: Ensure new ntp server is being synced to
        another external time source
        @tms_test_steps:
            @step: 1 Create the ntp external server item
            @result: Ntp server item created
            @step: 2 Create and run the plan
            @result: Plan created and run successfully
            @step: 3 Check the /etc/ntp.conf for the server
            @result: /etc/ntp.conf contains the server
            @step: 4 run ntpstat on the ms to ensure ntp re-syncs
            @result: Ntp service is synced to the external server loopback
                address
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # Step 1: Call the ntp sync method
        self.ntp_syncs_with_server(
            server="server='1.ie.pool.ntp.org'",
            item_to_grep=r"server 1.ie.pool.ntp.org",
            server_name="/server_220_b")

    @attr('all', 'non-revert')
    def test_04_p_ntp_updates_server(self):
        """
        @tms_id: litpcds_220_tc04
        @tms_requirements_id: LITPCDS-220
        @tms_title: ntp updates server
        @tms_description: Ensure updated ntp server is syncing to new address
        @tms_test_steps:
            @step:  Setup, create and run the initial plan
            @result:Plan is created and runs successfully
            @step:  Ensure ntp server is created
            @result:ntp server is created
            @step:  Update the server
            @result:Server is updated
            @step:  Check the /etc/ntp.conf for the new server
            @result:The /etc/ntp.conf for the new server
            @step:  Run ntpstat on the ms
            @result:Ntpstat runs successfully
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        # Step 1: Setup, create and run the initial plan
        # change the paths and variables needed
        ntp_external_server = "server='1.ie.pool.ntp.org'"

        # create the ntp server item
        ntp_server = self.find(self.ms_node, "/software",
                        "ntp-server", False)[0]
        ntp_server_url = ntp_server + '/server_220_c'
        self.execute_cli_create_cmd(self.ms_node, ntp_server_url, "ntp-server",
                                    ntp_external_server, add_to_cleanup=False)

        # create the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # set a timeout
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        # Wait for plan to complete with success
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, self.timeout_mins)
        # ensure plan was successful
        self.assertTrue(completed_successfully, "Plan was not successful")

        # Step 3: Update the server
        # create the ntp service item
        ntp_new_server = "server='2.ie.pool.ntp.org'"
        self.execute_cli_update_cmd(
            self.ms_node, ntp_server_url, ntp_new_server)

        # create the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        # Wait for plan to complete with success
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, self.timeout_mins)
        # ensure plan was successful
        self.assertTrue(completed_successfully, "Plan was not successful")

        # wait until the next puppet cycle
        puppet_cycle = self.get_puppet_interval(self.ms_node)
        time.sleep(puppet_cycle)

        # Step 4: Check the /etc/ntp.conf for the server
        grep_for = r"server 2.ie.pool.ntp.org"
        # execute grep command
        cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, grep_for)
        std_out, std_err, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, exit_code)
        # check for the new server

        # Step 5: run ntpstat on the ms
        self.assertTrue(self.wait_for_cmd(self.ms_node, self.ntp_stat_cmd, 0,
                                          timeout_mins=5))
