# Member Import

This script allows to automatically add members to the space.

## Usage

First, you must create a CSV file to import members. CSV file must have two columns: **name** with member ID and __one__ of the following columns: 

- **eolymp_user_id** - User ID for Eolymp account
- **eolymp_username** - Username for Eolymp account
- **password** - password for space internal authorization server.  

If column **password** is specified member will be able to authorize using internal authorization server for the space. In this case, you must configure space's authorization server accordingly in the "Settings" section. 

An example of CSV file:

```csv
name,eolymp_username
foo,moo
bar,goo
```

This CSV defines two members: "foo" and "bar". Member "foo" will be able to log in using Eolymp account "moo" and member "bar" will be able to log in using Eolymp account "goo".

An example of CSV file with passwords:

```csv
name,password
foo,123123
```

This CSV defines single member: "foo". This member will be able to log in using space login form using username "foo" and password "123123".

Once you have prepared CSV file you have to save it with name `members.csv` and import it using `import-members.py` script. Execute this script with two environment variables:

- `EOLYMP_TOKEN` - API key or your access token
- `EOLYMP_SPACE` - __Key__ of the space where you want to add members

The script will automatically scan space for existing members and will automatically create or update existing members.

Execute script:

```shell
$ EOLYMP_TOKEN=etkn-... EOLYMP_SPACE=myspace python import-members.py
```
