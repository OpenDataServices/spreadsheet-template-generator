# Get started

Create and activate a Python virtual environment using your preferred method, e.g. for `pyenv`:

```python
pyenv virtualenv 3.12.3 spreadsheet-template-generator
pyenv activate spreadsheet-template-generator
```

Install requirements:

```python
pip install -r requirements.txt
```

Create a template using a JSON schema:

```python
python manage.py create-template path/to/schema.json
```
