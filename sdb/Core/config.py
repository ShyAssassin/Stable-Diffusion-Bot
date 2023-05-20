import json
import os
from pydantic import BaseModel, ValidationError, validate_model, validator


class Text2ImgConfig(BaseModel):
    device: str = "cuda"
    current_model: str = "andite/anything-v4.0"
    width: int = 512
    height: int = 512
    batch_size: int = 3
    sample_steps: int = 50
    guidance_scale: int = 7
    images_per_prompt: int = 1
    safety_checker: bool = True
    stack_horizontally: bool = True
    # the pipeline does not like working with arrays, so we should just join it and add ", " between each item before passing it to the pipeline
    # we use a list here because it is easier to work with when in json format
    base_prompts: list[str] = []
    negative_prompts: list[str] = [
        "(worst quality:1.4)",
        "(low quality:1.4)",
        "(monochrome:1.1)",
        "extra limbs",
        "mutation",
        "mutated",
    ]
    # we dont need to join this because we are just checking if the prompt is in the list
    banned_prompts: list[str] = []

    @validator("images_per_prompt")
    def prompts_per_prompt_valid(cls, v):
        if v < 1:
            raise ValueError("Images per prompt must be greater than 0")
        return v

    @validator("current_model")
    def model_valid(cls, v):
        if v == "":
            raise ValueError("A valid model must be defined")
        return v

    @validator("batch_size")
    def batchsize_valid(cls, v):
        if v < 1:
            raise ValueError("Batch size must be greater than 0")
        return v

    @validator("device")
    def device_valid(cls, v):
        if v not in ["cuda", "cpu"]:
            raise ValueError("Device must be either cuda or cpu")
        return v

    @validator("sample_steps")
    def sample_steps_valid(cls, v):
        if v < 1:
            raise ValueError("Sample steps must be greater than 0")
        return v


class SDBConfig(BaseModel):
    version: int = 2
    debug: bool = False
    save_images: bool = False
    command_prefix: str = "*"
    available_models: list[str] = [
        "andite/anything-v4.0",
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
    ]
    Text2Img: Text2ImgConfig = Text2ImgConfig()

    def save(self, file: str = "config.json"):
        with open(file, "w") as f:
            json.dump(obj=self.dict(), fp=f, indent=4)

    def load(self, file: str = "config.json") -> None:
        if not os.path.exists(file):
            print("config file not found, creating one")
            self.save(file)
        else:
            try:
                self.__dict__.update(self.parse_file(file))
                self.validate(self)
                self.save(file)
            except (ValidationError, Exception) as e:
                print(f"Invalid Data found in config.json please fix all config issues before continuing \n {e}")
                exit(1)

    def update(self, data) -> None:
        try:
            values, fields, error = validate_model(self.__class__, data)
            if error:
                raise error
            for name in fields:
                value = values[name]
                print("set object data -- %s => %s", name, value)
                setattr(self, name, value)
            # Once all new values are set save just incase we crash somewhere
            self.save()
        except (ValidationError, Exception):
            print("Failed to update config with new values!")
