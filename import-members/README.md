# Member Import

This script allows to automatically add members to the space.

## Usage

This script requires environment variable `EOLYMP_TOKEN` with an [API key](https://developer.eolymp.com/) or your access token.

Execute script with `space-key` and `input-filename` arguments.

```shell
$ EOLYMP_TOKEN=etkn-... python import_members.py myspace members.csv
```

The script will read `members.csv` file and add or update members in the space. The file format is described below.

### Format

Depending on the [identity provider](https://support.eolymp.com/coaching/members/identity-provider) you are using, the CSV file must contain different columns.

If you want to use **Eolymp Identity Provider**, the CSV file must contain column **eolymp_username** with username for Eolymp account. The rest of the profile information will be automatically fetched from Eolymp.

If you want to use **Space Identity Provider** server, the CSV file may contain the following columns:

- **nickname** (required) - nickname for the member (login)  
- **name** - full name
- **password** - password for internal authorization server
- **email** - email address
- **country** - two-letter country code, for example: `ua`, `es` or `az`.

For either identity provider, you can add additional information:

- **inactive** - yes/no flag to mark member as inactive
- **unofficial** - yes/no flag to mark member as unofficial
- **groups** - space separated list of group IDs
- **attr_\<key\>** - additional [profile fields](https://support.eolymp.com/coaching/members/configure-profile), where `<key>` is the attribute key 

An example of CSV file for Eolymp Identity Provider:

```csv
eolymp_username,inactive,attr_university,attr_year
foo,no,MIT,2019
bar,yes,Harvard,2020
```


