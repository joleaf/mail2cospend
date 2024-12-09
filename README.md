# Mail2Cospend

A workflow for publishing eBons from mail to Cospend (App in Nextcloud).
Uses [uv](https://github.com/astral-sh/uv) for Python project management.

## Quick start

### Install mail2cospend

```shell
pip install mail2cospend
```

### Run the command

```shell
mail2cospend --help
```

```
Usage: mail2cospend [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  project-infos  Only print information about the cospend project...
  run            Run the service.
  show-config    Print the current config.         
```

### Configuration with environment variables

Change them in the [.env](.env) file.

| Variable                        | Description                                                                                                                 | Type               |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------|--------------------|
| COSPEND_PROJECT_URL             | The url of the cospend project (shared link in the project)                                                                 | string             |
| COSPEND_PROJECT_PASSWORD        | The (optional) password of the cospend project (if set)                                                                     | string             |
| COSPEND_PAYED_FOR_DEFAULT       | The ids of the payed for users, seperated by a ","                                                                          | string             |
| COSPEND_PAYED_FOR_{adapter}     | The ids of the payed for users, seperated by a "," for a specified *adapter* (^1)                                           | string             |
| COSPEND_PAYER_DEFAULT           | The id of the payer                                                                                                         | string             |
| COSPEND_PAYER_{adapter}         | The id of the payer for a specified *adapter* (^1)                                                                          | string             |
| COSPEND_CATEGORYID_DEFAULT      | The id of the category                                                                                                      | string             |
| COSPEND_CATEGORYID_{adapter}    | The id of the category for a specified *adapter* (^1)                                                                       | string             |
| COSPEND_PAYMENTMODEID_DEFAULT   | The id of the payment mode                                                                                                  | string             |
| COSPEND_PAYMENTMODEID_{adapter} | The id of the payment mode for a specified *adapter* (^1)                                                                   | string             |
| ADAPTER_{adapter}_ENABLED       | Enable or diable the specified *adapter* (^1), default is TRUE                                                              | boolean            |
| NTFY_URL                        | The url of the [ntfy](https://ntfy.sh/) server. If not set it is disabled.                                                  | string             |
| NTFY_BEARER_AUTH_TOKEN          | The (optional) bearer auth token for the ntfy server.                                                                       | string             |
| NTFY_TOPIC                      | The topic for the ntfy notifications.                                                                                       | string             |
| NTFY_MESSAGE_TEMPLATE           | The message template for the ntfy notifications. Use the {adapter}/{document}/{timestamp}/{sum} variables in this template. | string             |
| IMAP_HOST                       | The IMAP host                                                                                                               | string             |
| IMAP_USER                       | The IMAP user                                                                                                               | string             |
| IMAP_PASSWORD                   | The IMAP password                                                                                                           | string             |
| IMAP_PORT                       | The IMAP port                                                                                                               | int (default: 993) |
| IMAP_INBOX                      | 'Inbox' of of the IMAP server                                                                                               | string             |
| SINCE                           | 'today' or a ISO date, if 'today', then the script will use always the current day                                          | str or ISO date    |
| INTERVAL                        | The request interval in seconds                                                                                             | int (default: 60)  |
| LOGLEVEL                        | The loglevel (DEBUG,INFO,WARING,ERROR)                                                                                      | string             |

^1) Use the values of the adapter names: REWE, NETTO, PICNIC, PLANTED, EDEKA, IKEA

## Development

1. Checkout this project
2. Install requirements

```shell
uv sync
uv lock
```

### Run with Python >= 3.12

```bash
uv run mail2cospend run
```

Use `--dry` to perform a "dry run": only request and parse bon from the mail inbox without publishing them to cospend.

If you want infos about your project (e.g., the available ids), run:

```
uv run mail2cospend project-infos
```

If you want infos about your current config, run:

```
uv run mail2cospend show-config
```

### Run with Docker

```bash
./build.sh
./run.sh
```

### Implemented adapters

- Rewe
- Netto
- Picnic
- Planted
- Edeka
- Ikea

