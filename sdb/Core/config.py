import json
import os
from pydantic import BaseModel, ValidationError, validate_model


class DiffusionPipelineConfig(BaseModel):
    device: str = "cuda"
    current_model: str = "andite/anything-v4.0"
    available_models: list[str] = [
        "andite/anything-v4.0",
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
    ]
    width: int = 512
    height: int = 512
    batch_size: int = 3
    sample_steps: int = 50
    guidance_scale: int = 7
    images_per_prompt: int = 1
    safety_checker: bool = True
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
    banned_prompts: list[str] = []


class SDBConfig(BaseModel):
    version: int = 2
    debug: bool = False
    save_images: bool = False
    private_bot: bool = False
    allowed_guilds: list[int] = []
    DiffusionPipeline: DiffusionPipelineConfig = DiffusionPipelineConfig()

    def save(self, file: str = "config.json"):
        with open(file, "w") as f:
            json.dump(obj=self.dict(), fp=f, indent=4)

    def load(self, file: str = "config.json") -> None:
        if not os.path.exists(file):
            print("config file not found, creating one")
            self.save(file)
        else:
            try:
                # since we are loading a full config it is fine for us to just update the entire dict because we assume
                # that the data is valid, if there are extra or missing fields in the config by default pydantic will
                # fill them in with default values.
                # if we want to "update" parts of the config at runtime we should use `setattr` so we can retain
                # previous values and only update values that have been "requested" to be changed
                self.__dict__.update(self.parse_file(file))
                self.validate(self)
            except (ValidationError, Exception):
                print("Invalid Data found in config, replacing with default values")

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
