import pytest
import requests
import random
import uuid

BASE_URL = "https://qa-internship.avito.com"


@pytest.fixture(scope="module")
def test_id():
    return random.randint(111111, 999999)


@pytest.fixture
def payload(test_id):
    return {
        "sellerID": test_id,
        "name": f"Тестовый товар {random.randint(1, 1000)}",
        "price": random.randint(100, 10000),
        "statistics": {
            "likes": random.randint(0, 100),
            "viewCount": random.randint(0, 1000),
            "contacts": random.randint(0, 10)
        }
    }


@pytest.fixture
def created_item(payload):
    response = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert response.status_code == 200, f"Ошибка создания объявления: {response.text}"
    response_data = response.json()
    item_id = response_data['status'].split(' - ')[-1]
    item_data = {"id": item_id}

    yield item_data

    if item_id:
        delete_response = requests.delete(f"{BASE_URL}/api/2/item/{item_id}")
        assert delete_response.status_code in [200, 404]


# полный жизненный цикл объявления

def test_full_lifecycle(payload, test_id):
    """TC-001: Тестирование полного жизненного цикла объявления."""
    create_response = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert create_response.status_code == 200
    created_item_data = create_response.json()

    item_id = created_item_data['status'].split(' - ')[-1]
    assert item_id is not None, "Не удалось извлечь ID из ответа на создание"

    get_response = requests.get(f"{BASE_URL}/api/1/item/{item_id}")
    assert get_response.status_code == 200
    get_item_data = get_response.json()[0]
    assert get_item_data["id"] == item_id
    assert get_item_data["sellerId"] == test_id

    get_by_seller_response = requests.get(f"{BASE_URL}/api/1/{test_id}/item")
    assert get_by_seller_response.status_code == 200
    seller_items = get_by_seller_response.json()
    assert isinstance(seller_items, list)
    assert any(item['id'] == item_id for item in seller_items), "Созданный товар не найден в списке товаров продавца"

    get_stats_response = requests.get(f"{BASE_URL}/api/2/statistic/{item_id}")
    assert get_stats_response.status_code == 200
    stats_data = get_stats_response.json()[0]
    assert "likes" in stats_data
    assert "viewCount" in stats_data
    assert "contacts" in stats_data


    delete_response = requests.delete(f"{BASE_URL}/api/2/item/{item_id}")
    assert delete_response.status_code == 200

    get_deleted_response = requests.get(f"{BASE_URL}/api/1/item/{item_id}")
    assert get_deleted_response.status_code == 404

# негативные тесты

def test_create_item_missing_name(payload):
    del payload["name"]
    response = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert response.status_code == 400


def test_create_item_invalid_price_type(payload):
    payload["price"] = "очень дорого"
    response = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert response.status_code == 400


def test_create_item_empty_body():
    response = requests.post(f"{BASE_URL}/api/1/item", json={})
    assert response.status_code == 400


def test_get_item_non_existent_id():
    non_existent_id = str(uuid.uuid4())
    response = requests.get(f"{BASE_URL}/api/1/item/{non_existent_id}")
    assert response.status_code == 404


def test_get_item_invalid_id_format():
    response = requests.get(f"{BASE_URL}/api/1/item/12345")
    assert response.status_code == 400


def test_get_items_for_non_existent_seller():
    non_existent_seller_id = random.randint(1000000, 2000000)
    response = requests.get(f"{BASE_URL}/api/1/{non_existent_seller_id}/item")
    assert response.status_code == 200
    assert response.json() == [], "Ожидался пустой список для несуществующего продавца"



def test_delete_non_existent_item():
    non_existent_id = str(uuid.uuid4())
    response = requests.delete(f"{BASE_URL}/api/2/item/{non_existent_id}")
    assert response.status_code == 404


def test_double_delete_item(created_item):
    item_id = created_item["id"]

    first_delete_response = requests.delete(f"{BASE_URL}/api/2/item/{item_id}")
    assert first_delete_response.status_code == 200

    second_delete_response = requests.delete(f"{BASE_URL}/api/2/item/{item_id}")
    assert second_delete_response.status_code == 404