# Mail2Cospend

Personal eBons from mail to Cospend (Nextcloud) workflow.
Uses [uv](https://github.com/astral-sh/uv) for Python project management.

## Install requirements

```shell
uv sync
uv lock
```

## Run with Python >= 3.12

```bash
uv run mail2cospend
```

Use `-dry` to perform a "dry run": only request and parse bon from the mail inbox without publishing them to cospend.

## Run with Docker

```bash
./build.sh
./run.sh
```

## Implemented adapters

- Rewe
- Netto
- Picnic

## Configuration with environment variables

Change them in the [.env](.env) file.

| Variable                      | Description                                                                                                                                    | Type                      |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| COSPEND_PROJECT_URL           | The url of the cospend project (shared link in the project), e.g., 'https://cloud.server.de/index.php/apps/cospend/api/projects/<myprojectid>' | string                    |
| COSPEND_PROJECT_PASSWORD      | The (optional) password of the cospend project (if set)                                                                                        | string (default: no-pass) |
| COSPEND_PAYED_FOR             | The ids of the payed for users, seperated by a ","                                                                                             | string                    |
| COSPEND_PAYER                 | The id of the payer                                                                                                                            | string                    |
| COSPEND_CATEGORYID_DEFAULT    | The id of the category                                                                                                                         | int                       |
| COSPEND_PAYMENTMODEID_DEFAULT | The id of the payment mode                                                                                                                     | int                       |
| IMAP_HOST                     | The IMAP host                                                                                                                                  | string                    |
| IMAP_USER                     | The IMAP user                                                                                                                                  | string                    |
| IMAP_PASSWORD                 | The IMAP password                                                                                                                              | string                    |
| IMAP_PORT                     | The IMAP port                                                                                                                                  | int (default: 993)        |
| IMAP_INBOX                    | 'Inbox' of of the IMAP server                                                                                                                  | string                    |
| SINCE                         | 'today' or a ISO date, if 'today', then the script will use always the current day                                                             | str or ISO date           |
| INTERVAL                      | The request interval in seconds                                                                                                                | int                       |
| LOGLEVEL                      | The loglevel (DEBUG,INFO,WARING,ERROR)                                                                                                         | string                    |
