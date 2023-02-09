class MockSSH:
    def set_missing_host_key_policy(self, policy):
        pass
    def connect(self, public_ip_address, username, key_filename, look_for_keys):
        pass

    def exec_command(self, command):
        return '', 'true\n', ''