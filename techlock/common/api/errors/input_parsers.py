

def parse_fields_string(fields):
    '''
        Parses the `fields` string and returns include_fields, exclude_fields lists
        A field will be excluded if it's prefixed with `!` otherwise it's included.

        Args:
            fields (str): CSV string of fields.
        Returns:
            include_fields (list): A list containing all fields to include.
            exclude_fields (list): A list containing all fields to exclude.

    '''
    include_fields = list()
    exclude_fields = list()
    if fields is not None:
        for field in fields.split(','):
            field = field.strip()
            if field.startswith('!'):
                exclude_fields.append(field[1:])
            else:
                include_fields.append(field)

    return include_fields, exclude_fields
