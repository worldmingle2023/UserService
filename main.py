from fastapi import FastAPI

app = FastAPI()


from enum import Enum
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}    

@app.get("/")
async def root():
    return {"message": "Hello"}



@app.get("/users")
async def get_all_users():
    return {"users": "users"}

@app.get("/user/{user_id}")
async def get_all_users(user_id: int):
    return {"user": user_id}