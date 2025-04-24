import os
import yaml
import random
import string
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from pydantic import BaseModel


def to_camel_case(snake_str: str) -> str:
    return "".join(word.capitalize() for word in snake_str.split("_"))


def generate_model_code(
        section: str,
        data: Any,
        generated: Dict[str, str],
        used_names: Set[str]
) -> Tuple[str, str]:
    class_name = to_camel_case(section) + "Model"
    original_name = class_name
    index = 1
    while class_name in used_names:
        class_name = f"{original_name}{index}"
        index += 1
    used_names.add(class_name)

    if not isinstance(data, dict):
        return "Any", ""

    fields = ""
    nested_code = ""

    for key, value in data.items():
        if isinstance(value, dict):
            nested_class_name, nested_def = generate_model_code(
                f"{section}_{key}", value, generated, used_names
            )
            fields += f"    {key}: Optional[{nested_class_name}] = None\n"
            nested_code += nested_def
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                nested_class_name, nested_def = generate_model_code(
                    f"{section}_{key}", value[0], generated, used_names
                )
                fields += f"    {key}: Optional[List[{nested_class_name}]] = None\n"
                nested_code += nested_def
            else:
                elem_type = type(value[0]).__name__ if value else "Any"
                fields += f"    {key}: Optional[List[{elem_type}]] = None\n"
        else:
            py_type = type(value).__name__ if value is not None else "str"
            fields += f"    {key}: Optional[{py_type}] = None\n"

    class_def = f"class {class_name}(BaseModel):\n{fields or '    pass'}\n\n"
    generated[class_name] = class_def
    return class_name, nested_code + class_def


def generate_pydantic_models(settings_path: str, env: str = "DEV", url_templates: Optional[List[str]] = None) -> None:
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Файл '{settings_path}' не найден.")

    with open(settings_path, "r") as f:
        config_yaml = yaml.safe_load(f)

    env_config = config_yaml.get(env)
    if not env_config:
        raise ValueError(f"Окружение '{env}' не найдено в конфигурации.")

    imports = {"from typing import Optional, List, Any", "from pydantic import BaseModel"}
    generated_models: Dict[str, str] = {}
    used_names: Set[str] = set()
    root_fields = ""
    nested_all_code = ""

    for section, data in env_config.items():
        class_name, nested_code = generate_model_code(section, data, generated_models, used_names)
        root_fields += f"    {section}: Optional[{class_name}] = None\n"
        nested_all_code += nested_code

    if url_templates:
        for tmpl in url_templates:
            root_fields += f"    {tmpl}_url: Optional[str] = None\n"

    settings_model = f"class Settings(BaseModel):\n{root_fields or '    pass'}\n\n"

    full_code = "\n".join(sorted(imports)) + "\n\n" + nested_all_code + settings_model

    filename = "".join(random.choices(string.ascii_lowercase + string.digits, k=6)) + ".py"
    file_path = os.path.join(os.path.dirname(os.path.abspath(settings_path)), filename)

    with open(file_path, "w") as f:
        f.write(full_code)

    print(f"Сгенерирован файл Pydantic-моделей: {file_path}")


if __name__ == "__main__":
    generate_pydantic_models(
        settings_path="src/config/settings.yml",
        env="DEV",
        url_templates=["postgresql", "redis", "nats"]
    )
