import imp
from itertools import product
from multiprocessing import connection
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
import requests
from fastapi.background import BackgroundTasks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

# This will be a different db (Each microservice needs diff db)
redis = get_redis_connection(
    host="redis-14480.c14.us-east-1-3.ec2.cloud.redislabs.com",
    port=14480,
    password="Vc4cRWecCQ8glxEP0kKCSzaEZdMLSM6L",
    decode_responses=True
)


class Order(HashModel):
    product_id:str
    price:float
    fee:float
    total:float
    quantity:int
    status:str #Pending, completed, refunded 

    class Meta:
        database = redis


@app.post('/orders')
async def create(request: Request, background_tasks:BackgroundTasks):  # Send ID, quantity 
    body = await request.json()

    req = requests.get("http://localhost:8000/products/{}".format(body['id']))
    
    product = req.json()
    print(product)
    order = Order(
        product_id = body['id'],
        price=product['price'],
        fee =0.2 * product['price'],
        total =1.2 * product['price'],
        quantity=body['quantity'],
        status = 'pending'
    )

    order.save()

    background_tasks.add_task(order_completed, order)  # this background task will continue to work, & sends status as pending initially 
    return order


def order_completed(order: Order):
    time.sleep(5)
    order.status = "Completed"
    order.save()
    redis.xadd('order_completed', order.dict(), '*')


@app.get('orders/{pk}')
def get(pk:str):
    return Order.get(pk=pk)