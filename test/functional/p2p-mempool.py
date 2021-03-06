#!/usr/bin/env python3
# Copyright (c) 2015-2016 The Bitcoin Core developers
# Copyright (c) 2019  Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.

from test_framework.mininode import *
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
import time
import contextlib

# This test checks different cases of handling mempool requests.
# If a peer is not whitelisted:
    # If rejectmempoolrequest=true, mempool request is always rejected.
    # If rejectmempoolrequest=false (default value), mempool request is rejected only if peerbloomfilters=0.
# Is a peer is whitelisted, mempool request is never rejected.

class P2PMempoolTests(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1

    def setup_network(self):
        self.setup_nodes()

    def setup_nodes(self):
        self.add_nodes(self.num_nodes)

    def run_test(self):
        @contextlib.contextmanager
        def run_connection(connection, title):
            logger.debug("setup %s", title)

            connections = [NodeConn('127.0.0.1', p2p_port(0), self.nodes[0], connection)]
            connection.add_connection(connections[0])
            thr = NetworkThread()
            thr.start()
            connection.wait_for_verack()

            logger.debug("before %s", title)
            yield
            logger.debug("after %s", title)

            connections[0].close()
            del connections
            thr.join()
            disconnect_nodes(self.nodes[0],1)
            self.stop_node(0)
            logger.debug("finished %s", title)

        def runTestWithParams(description, args, expectedReject):
            self.start_node(0, args)
            connection = NodeConnCB()
            with run_connection(connection, description):
                # request mempool
                connection.send_message(msg_mempool())
                if not expectedReject:
                    time.sleep(1)
                    # mininode must not be disconnected at this point
                    assert_equal(len(self.nodes[0].getpeerinfo()), 1)
                else:
                    connection.wait_for_disconnect()
                    # mininode must be disconnected at this point
                    assert_equal(len(self.nodes[0].getpeerinfo()), 0)

        test_cases = [
            ["Scenario: peerbloomfilters=0, rejectMempoolRequests=false (default), not whitelisted", ['-peerbloomfilters=0'], True],
            ["Scenario: peerbloomfilters=1, rejectMempoolRequests=false (default), not whitelisted", ['-peerbloomfilters=1'], False],
            ["Scenario: peerbloomfilters=0, rejectMempoolRequests=true, not whitelisted", ['-peerbloomfilters=0', '-rejectmempoolrequest=1'], True],
            ["Scenario: peerbloomfilters=1, rejectMempoolRequests=true, not whitelisted", ['-peerbloomfilters=1', '-rejectmempoolrequest=1'], True],
            ["Scenario: peerbloomfilters=0, rejectMempoolRequests=false (default), whitelisted", ['-peerbloomfilters=0', '-whitelist=127.0.0.1'], False],
            ["Scenario: peerbloomfilters=1, rejectMempoolRequests=false (default), whitelisted", ['-peerbloomfilters=1', '-whitelist=127.0.0.1'], False],
            ["Scenario: peerbloomfilters=0, rejectMempoolRequests=true, whitelisted", ['-peerbloomfilters=0', '-rejectmempoolrequest=1', '-whitelist=127.0.0.1'], False],
            ["Scenario: peerbloomfilters=1, rejectMempoolRequests=true, whitelisted", ['-peerbloomfilters=1', '-rejectmempoolrequest=1', '-whitelist=127.0.0.1'], False]
        ]

        for test_case in test_cases:
            runTestWithParams(test_case[0], test_case[1], test_case[2])

if __name__ == '__main__':
    P2PMempoolTests().main()
