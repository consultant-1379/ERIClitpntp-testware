"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Sep 2019
@author:    Karen Flannery
@summary:   TORF-370237: As a LITP engineer, I need to update a number
            of properties so that they support dual stack with a CIDR
            prefix
"""
from litp_generic_test import GenericTest, attr
import test_constants as const


class Story370237(GenericTest):
    """
    TORF-370237:
    As a LITP engineer, I need to update a number of properties so
    that they support dual stack with a CIDR prefix
    """

    def setUp(self):
        """
        Runs before every single test
        """
        super(Story370237, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = [self.ms_node] + self.peer_nodes
        self.software_items = self.find(self.ms_node, '/software',
                                        'software-item', False)[0]
        self.node_urls = ["/ms"] + self.find(self.ms_node, '/deployments',
                                             'node')
        self.list_of_ntp_services = self.find(self.ms_node, '/software',
                                              'ntp-service',
                                              assert_not_empty=False)
        self.ntp_service_name = "ntp-ipv6"
        self.ntp_ipv6_service_url = "{0}/{1}".format(self.software_items,
                                                     self.ntp_service_name)
        self.ntp_ipv6_server_url = "{0}/servers/{1}"
        self.ipv6_address = "fdde:4d7e:d471:1::835:90:103"
        self.ipv6_prefix = "64"
        self.ipv6_address_update = "2001:1b70:6207:5f:0:4048:6666:2f"
        self.ipv6_prefix_update = "128"
        self.default_ms_address = "127.127.1.0"
        self.default_peer_nodes_address = "192.168.0.42"
        self.props = "server={0}"
        self.plan_timeout = 5

    def tearDown(self):
        """
        Runs after every single test
        """
        super(Story370237, self).tearDown()

    def check_ntp_config(self, expected_ip_address, prefix, nodes):
        """
        Description:
             Checks the /etc/ntp.conf file(s) for a specified IP
             address on specified nodes
        Args:
            expected_ip_address (str): The expected IP address to be
                                       found in /etc/ntp.conf is
                                       matched in the file
            prefix (str): IPv6 prefix
            nodes (list): list of nodes to check
        """

        grep_ntp_config_cmd = "{0} {1} {2} | {3} '{{print $2}}' | {0} -v '#'"\
            .format(const.GREP_PATH, expected_ip_address, const.NTPD_CFG_FILE,
                    const.AWK_PATH)

        for node in nodes:
            ip_addresses = self.run_command(node, grep_ntp_config_cmd,
                                        su_root=True, default_asserts=True)[0]
            self.assertEqual(expected_ip_address, ip_addresses[0],
                    "Expected IP address {0} is not the same as actual IP "
                    "address {1}".format(expected_ip_address, ip_addresses[0]))
            self.assertNotEqual("{0}/{1}".format(expected_ip_address,
                                                 prefix), ip_addresses[0],
                        "IPv6 Address with prefix is present in /etc/ntp.conf")

    @attr('all', 'revert', 'story370237', 'story370237_tc01')
    def test_01_p_create_update_remove_ntp_server_ipv6_address(self):
        """
        @tms_id: torf_370237_tc01, torf_370237_tc04, torf_370237_tc11
        @tms_requirements_id: TORF-370237
        @tms_title: create update remove ntp server with IPv6_address
        @tms_description: Test to verify that ntp server address field
           supports an IPv6 address. Also if the address contains
           prefix, that it is stripped out before being written
            to /etc/ntp.conf file
        @tms_test_steps:
            @step: Remove any ntp-services if present
            @result: ntp-services are removed
            @step: Create ntp-server
            @result: ntp-server is created
            @step: Inherit ntp-service onto peer nodes
            @result: ntp-service is successfully inherited onto peer
                     nodes
            @step: Verify /etc/ntp.conf is updated without prefix
            @result: /etc/ntp.conf is updated without prefix
            @step: Update ntp-server address and verify /etc/ntp.conf
                   is updated
            @result: ntp-server address and /etc/ntp.conf is updated
            @step: Remove ntp-server and verify /etc/ntp.conf is
                   reverted to default address
            @result: ntp-server is removed and /etc/ntp.conf is
                     reverted to default address
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        self.log("info", "#1. Remove any ntp-services if present")
        if self.list_of_ntp_services:
            for ntp_service in self.list_of_ntp_services:
                self.execute_cli_remove_cmd(self.ms_node, ntp_service)
            self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                    self.plan_timeout)

        self.log("info", "#2. Create ntp-server")
        self.execute_cli_create_cmd(self.ms_node, self.ntp_ipv6_service_url,
                                    "ntp-service", add_to_cleanup=True)
        self.execute_cli_create_cmd(self.ms_node, self.ntp_ipv6_server_url.
                        format(self.ntp_ipv6_service_url, "server-ipv6"),
                        "ntp-server", self.props.format("{0}/{1}".format(
                self.ipv6_address, self.ipv6_prefix), add_to_cleanup=True))

        self.log("info", "#3. Inherit ntp-service onto peer nodes")
        for node_url in self.node_urls:
            self.execute_cli_inherit_cmd(self.ms_node, "{0}/items/{1}".format
            (node_url, self.ntp_service_name), self.ntp_ipv6_service_url,
                                         add_to_cleanup=True)
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                self.plan_timeout)

        self.log("info", "#4. Verify /etc/ntp.conf is updated without"
                         " prefix")
        self.check_ntp_config(self.ipv6_address, self.ipv6_prefix,
                              self.all_nodes)

        self.log("info", "#5. Update ntp-server address and verify"
                         " /etc/ntp.conf is updated")
        self.execute_cli_update_cmd(self.ms_node, self.ntp_ipv6_server_url
                .format(self.ntp_ipv6_service_url, "server-ipv6"), self.props
                                    .format("{0}/{1}".format(
            self.ipv6_address_update, self.ipv6_prefix_update),
            add_to_cleanup=True))
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                self.plan_timeout)
        self.check_ntp_config(self.ipv6_address_update,
                              self.ipv6_prefix_update, self.all_nodes)

        self.log("info", "#6. Remove ntp-server and verify /etc/ntp.conf is "
                         "reverted to default address")
        self.execute_cli_remove_cmd(self.ms_node, self.ntp_ipv6_service_url)
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                self.plan_timeout)
        self.check_ntp_config(self.default_ms_address,
                              self.ipv6_prefix_update, [self.ms_node])
        self.check_ntp_config(self.default_peer_nodes_address,
                              self.ipv6_prefix_update, self.peer_nodes)
