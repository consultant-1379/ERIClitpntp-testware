"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Febr 2017
@author:    xsteuli
@summary:   Integration tests for Story: TORF-166156
"""
from litp_generic_test import GenericTest, attr
from litp_generic_utils import GenericUtils
from redhat_cmd_utils import RHCmdUtils
import test_constants


class Story166156(GenericTest):
    """
    TORF-166156:
    As a LITP user, I want modelled NTP Server configurations to be applied to
    physical peer nodes , so that I can configure the nodes with my preference
    of NTP Servers
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
        super(Story166156, self).setUp()
        self.redhat = RHCmdUtils()
        self.gen_utils = GenericUtils()

        self.management_server = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.ms_ip = self.get_node_att(self.management_server, 'ipv4')

        self.node1 = self.mn_nodes[0]
        self.node2 = self.mn_nodes[1]
        self.node1_url = \
            self.get_node_url_from_filename(self.management_server,
                                            self.node1)
        self.node2_url = \
            self.get_node_url_from_filename(self.management_server,
                                            self.node2)
        self.node_urls = [self.node1_url, self.node2_url]

        self.ntp_stat_cmd = "/usr/bin/ntpstat"
        self.timeout_mins = 3
        self.grep_file = "/etc/ntp.conf"

        self.ntp_1_ip = '192.168.0.1'
        self.ntp_2_ip = 'ntpAlias1'
        self.ntp_3_ip = 'ntpAlias2'
        self.ntp_4_ip = '192.168.0.1'

        self.ntp_servers = [self.ntp_1_ip,
                            self.ntp_2_ip,
                            self.ntp_3_ip,
                            self.ntp_4_ip]

        self.expected_list = \
            ["server {0}".format(x) for x in self.ntp_servers]

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
        super(Story166156, self).tearDown()

    @attr('all', 'non-revert', 'story166156', 'story166156_tc01')
    def test_01_p_reconfigure_multiple_ntp_services_runtime(self):
        """
        @tms_id: torf_166156_tc01
        @tms_requirements_id: TORF-166156
        @tms_title: reconfigure multiple ntp services
        @tms_description: Positive test case that checks that multiple ntp
            services can be created inside software items path and inherited
            on peer nodes.
        @tms_test_steps:
            @step: Create node1 and node2 alias config.
            @result: alias config created for node1 and node2.
            @step: Create ntpAlias1(172.16.30.1) and ntpAlias2(172.16.29.1)
                   aliases on node1 and node2. ntpAlias1 and ntpAlias2 are
                   external ntp ip addresses present on the Cloud GW.
            @result: ntpAlias1 and ntpAlias2 added to node1 and node2.
            @step: Create ntp2 service with ntp_1_ip, ntp_2_ip, ntp_3_ip,
                   ntp_4_ip as ntp servers.
            @result: ntp2 service successfully created.
            @step: Inherit ntp2 service to node1 and node2.
            @result: ntp2 service successfully inherited.
            @step: Create and run litp plan.
            @result: litp plan run successfully.
            @step: Check ntp_1_ip, ntp_2_ip,_ntp_3,_ip ntp_4_ip are set as
                   ntp servers on node1 and node2.
            @result: ntp_1_ip, ntp_2_ip,_ntp_3,_ip ntp_4_ip are set as
                     ntp servers on node1 and node2.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # ntp2 ntp service name
        ntp2_svc_name = 'ntp2'

        # Get software items collection path
        software_items = self.find(self.management_server, '/software',
                                   'software-item', False)[0]
        ntp2_service_url = software_items + '/' + ntp2_svc_name
        ntp2_servers_url = ntp2_service_url + '/servers'

        # Create node1 and node2 alias_config
        self.execute_cli_create_cmd(self.management_server,
                                    self.node1_url + '/configs/alias_config',
                                    "alias-node-config", add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    self.node2_url + '/configs/alias_config',
                                    "alias-node-config", add_to_cleanup=False)

        # Create ntpAlias1 and ntpAlias2 on both peer nodes
        # ntpAlias1 and ntpAlias2 are external ntp ip addresses present on
        # the Cloud GW (eth2 =>172.16.30.1 ; eth3 => 172.15.29.1)
        props = "alias_names=ntpAlias1 address=172.16.30.1"
        self.execute_cli_create_cmd(self.management_server, \
                self.node1_url + '/configs/alias_config/aliases/ntpAlias1', \
                "alias", props, add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server, \
                self.node2_url + '/configs/alias_config/aliases/ntpAlias1', \
                "alias", props, add_to_cleanup=False)

        props = "alias_names=ntpAlias2 address=172.16.29.1"
        self.execute_cli_create_cmd(self.management_server, \
                self.node1_url + '/configs/alias_config/aliases/ntpAlias2', \
                "alias", props, add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server, \
                self.node2_url + '/configs/alias_config/aliases/ntpAlias2', \
                "alias", props, add_to_cleanup=False)

        # Create ntp2 service item
        self.execute_cli_create_cmd(self.management_server, \
                ntp2_service_url, "ntp-service", add_to_cleanup=False)

        # Create ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip
        # as ntp-servers inside ntp2 service
        i = 0
        for server in self.ntp_servers:
            props = "server={0}".format(server)
            self.execute_cli_create_cmd(self.management_server, \
                   ntp2_servers_url + '/server' + str(i + 1), "ntp-server", \
                   props, add_to_cleanup=False)
            i += 1

        # inherit ntp2 service on node1 and node2
        for node_url in self.node_urls:
            self.execute_cli_inherit_cmd(self.management_server, \
                    node_url + '/items/' + ntp2_svc_name, ntp2_service_url, \
                    add_to_cleanup=False)

        self.run_and_check_plan(self.management_server, \
                    test_constants.PLAN_COMPLETE, self.timeout_mins)

        for node in self.mn_nodes:
            # Grep "/etc/ntp.conf" file for the ntp servers list
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file,
                                                 self.ntp_servers)
            std_out, std_err, exit_code = self.run_command(node, cmd)
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)

            # Check ntp_1_ip, ntp_2_ip,_ntp_3,_ip ntp_4_ip
            # are set as ntp servers
            self.assertEqual(set(), \
                (self.gen_utils.compare_lists(self.expected_list, std_out)))

            # Run ntpstat on the peer nodes to ensure ntp re-syncs with the
            # newly added ntp servers
            self.assertTrue(self.wait_for_cmd(node, self.ntp_stat_cmd, \
                                              0, timeout_mins=30))

    @attr('all', 'non-revert', 'story166156', 'story166156_tc02')
    def test_02_p_remove_multiple_ntp_services_runtime(self):
        """
        @tms_id: torf_166156_tc02
        @tms_requirements_id: TORF-166156
        @tms_title: remove multiple ntp services runtime.
        @tms_description: Positive test case that will check that the
            inherited ntp service can be successfully removed from peer nodes.
        @tms_test_steps:
            @step: Remove ntp2 service from software items.
            @result: ntp2 service item is in ForRemoval state.
            @step: Create and run litp plan.
            @result: litp plan run successfully.
            @step: Check node1 and node2 use the default ntp
                   configuration (management server ip).
            @result: node1 and node2 use the default ntp configuration
                    (management server ip).
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # ntp2 ntp service name
        ntp2_svc_name = 'ntp2'

        # Get software item collection path
        software_items = self.find(self.management_server, \
                        '/software', 'software-item', False)[0]
        ntp2_service_url = software_items + '/' + ntp2_svc_name

        # Remove ntp2 service from software item path
        # Tasks will be created to remove the inherited ntp2
        # from node1 and node2
        self.execute_cli_remove_cmd(self.management_server, \
                            ntp2_service_url, add_to_cleanup=False)

        self.run_and_check_plan(self.management_server, \
                        test_constants.PLAN_COMPLETE, self.timeout_mins)

        # Check that default configuration is present after ntp2 service was
        # removed. Default ntp server will be the management server ip.
        # Grep "/etc/ntp.conf" file for the default management ip server on
        # node1 and node2.
        for node in self.mn_nodes:
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, self.ms_ip)
            std_out, std_err, exit_code = self.run_command(node, cmd)
            self.assertEqual(["server {0}".format(self.ms_ip)], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)

    @attr('all', 'non-revert', 'story166156', 'story166156_tc03')
    def test_03_p_inherit_ntp_server_set_to_ms_ip(self):
        """
        @tms_id: torf_166156_tc03
        @tms_requirements_id: TORF-166156
        @tms_title: inherit ntp server set to ms ip
        @tms_description: Positive test case that checks that ntp service that
                use the management server ip value as ntp server can be
                successfully created on peer nodes.
        @tms_test_steps:
            @step: Create ntp2 service with one ntp server set to the
                   management server ip value.
            @result: Plan ntp2 service successfully created.
            @step: Create and run litp plan.
            @result: litp plan run successfully.
            @step: Grep "/etc/ntp.conf" file for management server ip on
                   both peer nodes.
            @result: management server ip set as ntp server on both peer nodes.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # ntp2 ntp service name
        ntp2_svc_name = 'ntp2'

        # Get software items collection path
        software_items = self.find(self.management_server, '/software', \
                                   'software-item', False)[0]
        ntp2_service_url = software_items + '/' + ntp2_svc_name
        ntp2_servers_url = ntp2_service_url + '/servers'

        # Create ntp2 service having ntp server ip equal with
        # management server ip.
        self.execute_cli_create_cmd(self.management_server, \
                ntp2_service_url, "ntp-service", add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, \
                ntp2_servers_url + '/server1', "ntp-server", \
                "server={0}".format(self.ms_ip), add_to_cleanup=False)
        self.execute_cli_inherit_cmd(self.management_server, \
                self.node1_url + '/items/' + ntp2_svc_name, ntp2_service_url, \
                add_to_cleanup=False)

        self.run_and_check_plan(self.management_server, \
                test_constants.PLAN_COMPLETE, self.timeout_mins)

        # Grep "/etc/ntp.conf" file for the managment server ip on
        # node1 and node2.
        for node in self.mn_nodes:
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, self.ms_ip)
            std_out, std_err, exit_code = self.run_command(node, cmd)
            self.assertEqual(["server {0}".format(self.ms_ip)], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)

    @attr('all', 'non-revert', 'story166156', 'story166156_tc04')
    def test_04_p_inherit_ntp_service_peer_node_when_one_uses_default(self):
        """
        @tms_id: torf_166156_tc04
        @tms_requirements_id: TORF-166156
        @tms_title: inherit ntp service on one peer node when the other uses
                    default ntp configuration.
        @tms_description: Positive test case that checks that an ntp-service
                    item can be inherited on one peer node when the other peer
                    node uses the default ntp configuration.
        @tms_test_steps:
            @step: Update ntp2 service server1 ntp-server item ip from
                   management server ip to ntp_1_ip value.
            @result: server1 ntp-server from ntp2 service updated with
                     ntp_1_ip value.
            @step: Create ntp_2_ip, ntp_3_ip, ntp_4_ip as ntp-servers inside
                   ntp2 ntp-service.
            @result: ntp_2_ip, ntp_3_ip, ntp_4_ip successfully added as
                    ntp-servers inside ntp2 ntp-service.
            @step: Create and run litp plan.
            @result: litp plan run successfully.
            @step: Grep "/etc/ntp.conf" file on node1 to see if it has
                   ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip as ntp servers.
            @result: node1 has ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip as
                     ntp servers.
            @step: Grep "/etc/ntp.conf" file on node2 to see that it has the
                   default management server ip as ntp server.
            @result: node2 has the default configuration
                     (management server ip).
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # ntp2 ntp service name
        ntp2_svc_name = 'ntp2'

        # Get software items collection path
        software_items = self.find(self.management_server, \
                                   '/software', 'software-item', False)[0]
        ntp2_service_url = software_items + '/' + ntp2_svc_name
        ntp2_servers_url = ntp2_service_url + '/servers'

        # Update server1 ip from management server ip to ntp_1_ip value
        props = "server={0}".format(self.ntp_1_ip)
        self.execute_cli_update_cmd(self.management_server, \
                                    ntp2_servers_url + '/server1', props)

        # Create ntp_2_ip, ntp_3_ip, ntp_4_ip as ntp-servers inside
        # ntp2 ntp-service
        i = 1
        for server in self.ntp_servers:
            props = "server={0}".format(server)
            self.execute_cli_create_cmd(self.management_server, \
                   ntp2_servers_url + '/server' + str(i + 1), \
                   "ntp-server", props, add_to_cleanup=False)
            i += 1

        self.run_and_check_plan(self.management_server, \
                    test_constants.PLAN_COMPLETE, self.timeout_mins)

        # Grep "/etc/ntp.conf" file on node1 to see if it has
        # ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip as ntp servers
        cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, self.ntp_servers)
        std_out, std_err, exit_code = self.run_command(self.node1, cmd)
        self.assertEqual(set(), \
                (self.gen_utils.compare_lists(self.expected_list, std_out)))
        self.assertEqual([], std_err)
        self.assertEqual(0, exit_code)

        # Grep "/etc/ntp.conf" file on node2 to see that it has the
        # default management server ip as ntp server
        cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file, self.ms_ip)
        std_out, std_err, exit_code = self.run_command(self.node2, cmd)
        self.assertEqual(["server {0}".format(self.ms_ip)], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, exit_code)

    @attr('all', 'non-revert', 'story166156', 'story166156_tc05')
    def test_05_p_inherit_different_ntp_service_with_same_ntp_servers(self):
        """
        @tms_id: torf_166156_tc05
        @tms_requirements_id: TORF-166156
        @tms_title: inherit different ntp service with the same
                    ntp servers list
        @tms_description: Positive test case that checks that peer nodes can
                    inherit different ntp service items with the same ntp
                    servers list.
        @tms_test_steps:
            @step: Create ntp3 ntp-service with ntp_1_ip, ntp_2_ip, ntp_3_ip,
                   ntp_4_ip as ntp-servers.
            @result: ntp3 service created.
            @step: Inherit ntp3 ntp service to node2.
            @result: ntp3 inherited to node2.
            @step: Create and run litp plan.
            @result: litp plan run successfully.
            @step: Grep "/etc/ntp.conf" file on both peer nodes.
                   Check the ntp servers list is correct.
            @result: node1  and node2 have the same ntp servers list.
                This is expected as ntp2 and ntp3 have the same ntp servers.
            @step: Run ntpstat and check that node1 and node2 are synced.
            @result: node1 and node2 are synced.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        # ntp3 ntp service name
        ntp3_svc_name = "ntp3"

        # Get software item collection path
        software_items = self.find(self.management_server, \
                '/software', 'software-item', False)[0]
        ntp3_service_url = software_items + '/' + ntp3_svc_name
        ntp3_servers_url = ntp3_service_url + '/servers'

        # Create ntp3 ntp-service
        # Create ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip as ntp-servers
        # inside ntp3 ntp-service.
        # ntp2 and ntp3 have the same server list.
        self.execute_cli_create_cmd(self.management_server, \
                    ntp3_service_url, 'ntp-service', add_to_cleanup=False)
        i = 0
        for server in self.ntp_servers:
            props = "server={0}".format(server)
            self.execute_cli_create_cmd(self.management_server, \
                            ntp3_servers_url + '/server' + str(i + 1), \
                            "ntp-server", props, add_to_cleanup=False)
            i += 1

        # Inherit ntp3 ntp service to node2
        self.execute_cli_inherit_cmd(self.management_server, \
                self.node2_url + '/items/' + ntp3_svc_name, \
                ntp3_service_url, add_to_cleanup=False)

        self.run_and_check_plan(self.management_server, \
                    test_constants.PLAN_COMPLETE, self.timeout_mins)

        # Grep "/etc/ntp.conf" file on both peer nodes to see if it has
        # the same ntp servers(ntp_1_ip, ntp_2_ip, ntp_3_ip, ntp_4_ip)
        for node in self.mn_nodes:
            cmd = RHCmdUtils().get_grep_file_cmd(self.grep_file,
                                                 self.ntp_servers)
            std_out, std_err, exit_code = self.run_command(node, cmd)
            self.assertEqual(set(), \
                (self.gen_utils.compare_lists(self.expected_list, std_out)))
            self.assertEqual([], std_err)
            self.assertEqual(0, exit_code)

            # Run ntpstat on the peer nodes to ensure ntp re-syncs with the
            # newly added ntp servers
            self.assertTrue(self.wait_for_cmd(node, self.ntp_stat_cmd, \
                                              0, timeout_mins=30))
