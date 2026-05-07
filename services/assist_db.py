import json

def write(file, new_cred):
    with open(file, "r") as f:
        data = json.load(f)

    data.append(new_cred)

    with open(file, "w") as f:
        json.dump(data, f, indent=4)


async def load(file, cred):
    with open(file, "r") as f:
        data = json.load(f)

    return data[cred]
