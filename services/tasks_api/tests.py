import uuid

import boto3
import pytest
from fastapi import status
from moto import mock_dynamodb
from starlette.testclient import TestClient

from main import app
from models import Task, TaskStatus
from store import TaskStore


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """
    GIVEN
    WHEN health check endpoint is called with GET method
    THEN response with status 200 and body OK is returned
    """
    response = client.get("/api/health_check/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "OK"}


@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        client = boto3.client("dynamodb")
        table_name = "test-table"
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GS1PK", "AttributeType": "S"},
                {"AttributeName": "GS1SK", "AttributeType": "S"},
            ],
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GS1",
                    "KeySchema": [
                        {"AttributeName": "GS1PK", "KeyType": "HASH"},
                        {"AttributeName": "GS1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
            ],
        )
        yield table_name


def test_added_task_is_retrieved_by_id(dynamodb_table):
    repository = TaskStore(table_name=dynamodb_table)
    task = Task.create(uuid.uuid4(), "task", "john@doe.com")

    repository.add(task)

    assert repository.get_by_id(task_id=task.id, owner=task.owner) == task


def test_open_tasks_listed(dynamodb_table):
    repository = TaskStore(table_name=dynamodb_table)
    open_task = Task.create(uuid.uuid4(), "task", "john@doe.com")
    closed_task = Task(uuid.uuid4(), "task", TaskStatus.CLOSED, "john@doe.com")

    repository.add(open_task)
    repository.add(closed_task)

    assert repository.list_open(owner=open_task.owner) == [open_task]


def test_closed_tasks_listed(dynamodb_table):
    repository = TaskStore(table_name=dynamodb_table)
    open_task = Task.create(uuid.uuid4(), "task", "john@doe.com")
    closed_task = Task(uuid.uuid4(), "task", TaskStatus.CLOSED, "john@doe.com")

    repository.add(open_task)
    repository.add(closed_task)

    repository.list_closed(owner=open_task.owner) == [closed_task]
