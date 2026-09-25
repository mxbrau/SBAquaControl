# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/mxbrau/SBAquaControl/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                           |    Stmts |     Miss |   Cover |   Missing |
|------------------------------- | -------: | -------: | ------: | --------: |
| scripts/\_\_init\_\_.py        |        0 |        0 |    100% |           |
| scripts/load\_secrets.py       |       16 |       16 |      0% |      1-24 |
| scripts/sync\_sd\_card.py      |       67 |       67 |      0% |     8-108 |
| test/conftest.py               |       56 |        7 |     88% |35-37, 55, 77, 85-86 |
| test/gen\_schedule\_fixture.py |       49 |       49 |      0% |    21-181 |
| test/mock\_server.py           |      471 |      471 |      0% |    29-955 |
| test/test\_api\_parity.py      |      171 |       77 |     55% |84-99, 142-143, 348-349, 358-416, 420-444, 448 |
| test/test\_firmware\_build.py  |       27 |        2 |     93% |    32, 34 |
| test/test\_host\_unit.py       |       14 |        1 |     93% |        21 |
| test/test\_live\_contract.py   |       23 |        2 |     91% |     28-29 |
| test/test\_parity.py           |       12 |        0 |    100% |           |
| **TOTAL**                      |  **906** |  **692** | **24%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/mxbrau/SBAquaControl/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/mxbrau/SBAquaControl/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mxbrau/SBAquaControl/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/mxbrau/SBAquaControl/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fmxbrau%2FSBAquaControl%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/mxbrau/SBAquaControl/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.