# python-analyser

This is the source code of the [Watnwy](https://watnwy.com) Python analyser service.

The [Watnwy](https://watnwy.com) platform aims at solving problems like how to make sure things remain consistent over time in large codebases with people coming and leaving the team/organization/company quite often, with a technology landscape that evolves at a very fast pace ([more details in our documentation](https://doc.watnwy.com/)). One possible solution is to collaboratively state on **what should [not] be used and why** on an online platform, and to **connect it with your codebase** to make sure things are aligned. The Watnwy analysers are what makes this connection possible.

If you want to track automatically something that is not being tracked at the moment, we welcome every contribution 🙏

This service expects to receive **POST** commands to the endpoint **/analysis** with the JSON payload:

```
{
  "path": "<The path of the project to analyse>"
}
```

The output is a JSON formatted AnalysisEcoSystemResult object which is defined in [analyser/models.py](analyser/models.py).

## Quick start

### Prerequesites

#### Python

This is a pure Python 3.9 service.

One easy way to get a **Python 3.9** interpreter available on your machine is using pyenv which can be installed following this guide: [https://github.com/pyenv/pyenv#installation](https://github.com/pyenv/pyenv#installation).

Once you have pyenv installed and ready, here is the command to get Python 3.9:

```
# Install Python 3.9

pyenv install 3.9.4

# Since there is a .python-version in the repo, the right Python interpreter should be launched if you just run Python by being in the repo's directory

➜  python-analyser git:(main) ✗ python
Python 3.9.4 (default, May  7 2021, 10:40:14)
[Clang 11.0.3 (clang-1103.0.32.62)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

#### Poetry

You now have to install **Poetry** which is the tool we use to run, build and deploy this service.
You can get the installation instructions [here](https://python-poetry.org/docs/#installation).

#### Python dependencies

The last step is to get the project's dependency:

```
poetry install
```

### Run an analysis using the CLI

Once you've got everything set up, you can use the CLI to run a local analysis and get a list of all the objects that have been detected. The same core functions as the ones the [Watnwy](https://watnwy.com) platform call when it performs a code analysis on a new commit are called behind the scene.

```
poetry run python -m analyser -q .

python/click              - [None] (With versions provider: True)
python/fastapi            - ['0.65.1'] (With versions provider: True)
python/aiofiles           - ['0.7.0'] (With versions provider: True)
python/aiohttp            - ['3.7.4.post0'] (With versions provider: True)
python/black              - ['21.5b1'] (With versions provider: True)
python/elastic-apm        - ['6.1.3'] (With versions provider: True)
python/fastapi            - ['0.65.1'] (With versions provider: True)
python/flake8             - ['3.9.2'] (With versions provider: True)
python/mypy               - ['0.812'] (With versions provider: True)
python/orjson             - ['3.5.2'] (With versions provider: True)
python/pre-commit         - ['2.13.0'] (With versions provider: True)
python/pytest             - ['6.2.4'] (With versions provider: True)
python/pytest-asyncio     - ['0.15.1'] (With versions provider: True)
python/python-json-logger - ['2.0.1'] (With versions provider: True)
python/toml               - ['0.10.2'] (With versions provider: True)
python/typer              - ['0.3.2'] (With versions provider: True)
python/uvicorn            - ['0.13.4'] (With versions provider: True)
python/wrapt              - ['1.12.1'] (With versions provider: True)
```

### Run and call the service

You can also try out the service by running and calling it locally. In this case, this is exactly what the [Watnwy](https://watnwy.com) platform does when it analyses your code.

```
# Run the service on localhost:6000
poetry run uvicorn analyser.api:app --port 6000

# Try it out using httpie
http -v :6000/analysis path=`pwd`

POST /analysis HTTP/1.1
Accept: application/json, */*;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Content-Length: 50
Content-Type: application/json
Host: localhost:6000
User-Agent: HTTPie/2.4.0

{
    "path": "/work/python-analyser"
}


HTTP/1.1 200 OK
content-length: 1702
content-type: application/json
date: Thu, 20 May 2021 08:47:12 GMT
server: uvicorn

[
    {
        "name": "python",
        "objects": [
            {
                "name": "aiofiles",
                "version": "0.7.0",
                "versions_providers": [
                    {
                        "package_name": "aiofiles",
                        "type": "PypiReleases"
                    }
                ]
            },
            ...
        ]
    },
    ...
]
```

## Analyses

For the time being, this analyser gets to detect:
* the Python packages added via Poetry, only if the `poetry.lock` file is under version control
* the Python packages added via `setup.py`

## Contributing

If you want to contribute to this analyser, we can run the tests with:

```
poetry run pytest
```

We also leverage pre-commit which can be run with:

```
poetry run pre-commit -a
```
