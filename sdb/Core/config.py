import json
import os
from pydantic import BaseModel, ValidationError, validate_model, validator


class Model(BaseModel):
    name: str
    id: str
    # currently `local` is useless because the pip version of diffusers does not have local safetensor support yet
    # TODO: when the safetensor support is merged upstream add support for local models
    local: bool

    @validator("id")
    def id_valid(cls, v):
        if v == None or v == "":
            raise ValueError("Model ID's must be defined")
        return v


class BasePipelineConfig(BaseModel):
    enabled: bool = True
    device: str = "cuda"
    model: Model = Model(name="anything-v4.5", id="ckpt/anything-v4.5-vae-swapped", local=False)
    width: int = 512
    height: int = 512
    batch_size: int = 2
    sample_steps: int = 35
    guidance_scale: float = 7
    images_per_prompt: int = 1
    safety_checker: bool = True
    # the pipeline does not like working with arrays, so we should just join it and add ", " between each item before passing it to the pipeline
    # we use a list here because it is easier to work with when in json format
    base_prompts: list[str] = []
    negative_prompts: list[str] = [
        "low quality",
        "monochrome",
        "extra limbs",
        "mutation",
        "mutated",
    ]

    @validator("images_per_prompt")
    def images_per_prompt_valid(cls, v):
        if v < 1:
            raise ValueError("Images per prompt must be greater than 0")
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

    @validator("width")
    def width_valid(cls, v):
        if v < 1:
            raise ValueError("Width must be greater than 0")
        return v

    @validator("height")
    def height_valid(cls, v):
        if v < 1:
            raise ValueError("Height must be greater than 0")
        return v


class Text2ImgConfig(BasePipelineConfig):
    device: str = "cuda"
    model: Model = Model(name="anything-v4.5", id="ckpt/anything-v4.5-vae-swapped", local=False)
    custom_pipeline: str = "lpw_stable_diffusion"
    custom_pipeline_revision: str = "0.15.1"
    stack_horizontally: bool = True


class Img2ImgConfig(BasePipelineConfig):
    strength: float = 0.5
    resize_images: bool = True
    stack_horizontally: bool = True

    @validator("strength")
    def strength_valid(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Strength must be between 0 and 1")
        return v


class SDBConfig(BaseModel):
    version: int = 2
    debug: bool = True
    save_images: bool = False
    command_prefix: str = "*"
    banned_prompts: list[str] = []

    Text2Img: Text2ImgConfig = Text2ImgConfig()
    Img2Img: Img2ImgConfig = Img2ImgConfig()

    def save(self, file: str = "config.json"):
        with open(file, "w") as f:
            json.dump(obj=self.dict(), fp=f, indent=4)

    def load(self, file: str = "config.json"):
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


# models: list[Model] = [
#     Model(
#         name="anything-v4.0",
#         id="andite/anything-v4.0",
#         local=False,
#     ),
#     Model(
#         name="stable-diffusion-v1-4",
#         id="CompVis/stable-diffusion-v1-4",
#         local=False,
#     ),
#     Model(
#         name="stable-diffusion-v1-5",
#         id="runwayml/stable-diffusion-v1-5",
#         local=False,
#     ),
# ]
