class ResourceException(Exception):
    print('Missing or misconfigured resources. You need to call clean_up().')
    pass