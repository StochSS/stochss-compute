class MockSSH:
    def set_missing_host_key_policy(self, policy):
        pass
    def connect(self, public_ip_address, username, key_filename, look_for_keys):
        pass
    def close(self):
        pass
    def exec_command(self, command):
        class MockFD:
            class MockChannel:
                def recv_exit_status(self):
                    return 0
            def readlines(self):
                return ['true\n']
            channel = MockChannel()

        return MockFD(), MockFD(), MockFD()

