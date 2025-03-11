from backend.app.schemas.text_data_schema import (  # IListTextDataCreate,; IGroupReadWithUsers,
    ITextDataCreate,
    # ITextDataRead,
    # ITextDataRequest,
    # ITextDataReadNotVectors,
    ITextDataUpdate,
    ITextDataUpdateRequest,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
)

def merge_schemas(target_schema, update_schema, default_values):
    # Создаем новый словарь, который будет содержать объединенные поля
    merged_dict = {}

    # Итерируем по полям первой схемы
    for field_name, field_value in target_schema.__dict__.items():
        # Если поле существует во второй схеме, обновляем его значение
        if field_name in update_schema.__dict__:
            merged_dict[field_name] = update_schema.__dict__[field_name]
        # Если поле не существует во второй схеме, берем его значение из первой схемы
        else:
            merged_dict[field_name] = field_value

    # Итерируем по полям второй схемы
    for field_name, field_value in default_values.items():
        # Если поле не существует в первой схеме, добавляем его в объединенный словарь
        if field_name not in target_schema.__dict__:
            raise ValueError(f"Поле '{field_name}' отсутствует в первой схеме")
        merged_dict[field_name] = default_values[field_name]

    # Создаем новую схему Pydantic с объединенными полями
    merged_schema = target_schema.__class__(**merged_dict)
    return merged_schema

if __name__ == "__main__":
    upd_request = {
        "text": "strin22g",
        "url": "string",
        "source_name": "string",
        # "vector": [0],
    }
    obj_upd_request = ITextDataUpdateRequest(**upd_request)
    obj_create = ITextDataCreate(text='string', elastic_id="111", processed_urls_id="019566a1-ca57-7e18-bbc8-018dc1f304ce")
    default_values = {
        'elastic_id': "222", 
        'processed_urls_id':"019566a1-ca57-7e18-bbc8-018dc1f304ce"
    }
    print(obj_upd_request.model_dump())
    print(obj_create)
    print(merge_schemas(obj_create, obj_upd_request, default_values))
    
