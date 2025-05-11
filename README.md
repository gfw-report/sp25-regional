# Artifacts of "A Wall Behind A Wall: Emerging Regional Censorship in China"

This repo contains the source code, data, and documents for the S&P 2025 paper
[*A Wall Behind A Wall: Emerging Regional Censorship in China*](https://gfw.report/publications/sp25/en/).

It is designed to reproduce the entire PDF version of the paper, including all the figures and tables, from the source code and data.

## Install Dependencies

Create a python virtual environment with all necessary dependencies:

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Build Paper and Figures

Build the PDF of the paper and all the figures:

```sh
cd paper
make
```
