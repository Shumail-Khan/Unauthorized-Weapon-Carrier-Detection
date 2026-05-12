from app.core.association import is_linked

WEAPON_CLASSES = ["Gun", "Weapon"]
UNIFORM_CLASSES = ["Uniform"]
PERSON_CLASS = "Person"


def check_authorization(detections):

    persons = []
    weapons = []
    uniforms = []

    # Separate objects
    for d in detections:
        if d["class"] == PERSON_CLASS:
            persons.append(d["bbox"])
        elif d["class"] in WEAPON_CLASSES:
            weapons.append(d["bbox"])
        elif d["class"] in UNIFORM_CLASSES:
            uniforms.append(d["bbox"])

    unauthorized_found = False

    for person in persons:

        has_weapon = any(is_linked(person, w) for w in weapons)
        has_uniform = any(is_linked(person, u) for u in uniforms)

        if has_weapon and not has_uniform:
            unauthorized_found = True
            break

    return not unauthorized_found