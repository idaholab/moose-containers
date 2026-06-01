import yaml
from jinja2 import Template

# Load template values
values = {}
for name in ["packages"]:
    with open(f"{name}.yml", 'r') as f:
        values.update({f"{name}_{k}": v for k, v in yaml.safe_load(f).items()})

# Load template
with open("containers.yml") as f:
    template = Template(f.read())

# Render and output
output = template.render(**values)
print(output)
