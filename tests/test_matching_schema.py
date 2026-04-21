from __future__ import annotations

from sqlalchemy import inspect

from app.models.matching import Matching, MatchingSku, MatchingTag
from app.models.product import Product, ProductColor
from app.models.tag import Tag
from app.services.matching_service import MatchingService


def _mapped_column_name(model: type[object], attr_name: str) -> str:
    """读取 ORM 属性实际映射到数据库里的列名。"""
    return inspect(model).attrs[attr_name].columns[0].name


def test_matching_model_uses_production_columns() -> None:
    """搭配主表模型不应再映射线上不存在的旧字段。"""
    column_names = {column.name for column in Matching.__table__.columns}

    assert 'user_id' not in column_names
    assert 'tag_id' not in column_names
    assert 'remark' not in column_names
    assert _mapped_column_name(Matching, 'matching_tag_id') == 'matching_tag_id'


def test_matching_sku_model_maps_legacy_attrs_to_production_columns() -> None:
    """搭配 SKU 模型保留旧属性名，但实际访问真实字段。"""
    column_names = {column.name for column in MatchingSku.__table__.columns}

    assert 'angle' not in column_names
    assert _mapped_column_name(MatchingSku, 'matching_sku_id') == 'id'
    assert _mapped_column_name(MatchingSku, 'product_color_id') == 'color_id'
    assert _mapped_column_name(MatchingSku, 'product_id') == 'product_id'


def test_matching_tag_model_does_not_map_user_id() -> None:
    """搭配标签表真实结构没有 user_id。"""
    column_names = {column.name for column in MatchingTag.__table__.columns}

    assert 'user_id' not in column_names
    assert _mapped_column_name(MatchingTag, 'matching_tag_id') == 'matching_tag_id'


def test_tag_model_uses_production_columns() -> None:
    """场景/风格标签模型不能再映射线上不存在的旧字段。"""
    column_names = {column.name for column in Tag.__table__.columns}

    assert 'user_id' not in column_names
    assert 'display_flag' not in column_names
    assert _mapped_column_name(Tag, 'tag_id') == 'tag_id'


def test_extract_sku_list_keeps_product_id_when_present() -> None:
    """前端传入颜色和单品编号时，服务层要保留下来用于写真实表。"""
    result = MatchingService()._extract_sku_list(
        {'matchingSkuList': [{'colorId': 11, 'productId': 22, 'angle': 'front'}]}
    )

    assert result == [{'productColorId': 11, 'productId': 22, 'angle': 'front'}]


def test_product_models_use_java_schema_columns() -> None:
    """单品模型要和 Java 原项目的真实表字段一致。"""
    product_columns = {column.name for column in Product.__table__.columns}
    color_columns = {column.name for column in ProductColor.__table__.columns}

    assert 'user_id' not in product_columns
    assert 'picture_url' not in product_columns
    assert 'remark' not in product_columns
    assert _mapped_column_name(Product, 'category_tag_id') == 'category_tag_id'
    assert _mapped_column_name(Product, 'scene_tag_id') == 'scene_tag_id'
    assert _mapped_column_name(ProductColor, 'color_name') == 'name'
    assert 'front_image_url' in color_columns
    assert 'side_image_url' in color_columns
    assert 'back_image_url' in color_columns


def test_group_matching_rows_matches_java_matching_vo_shape() -> None:
    """试穿搭配列表需要返回 Java MatchingVO / MatchingEO 结构。"""
    rows = [
        {
            'matching_id': 1,
            'matching_name': '通勤套装',
            'matching_tag_id': 2,
            'matching_sku_id': 10,
            'product_id': 20,
            'product_color_id': 30,
            'color_front_img_url': 'https://example.com/front.png',
            'scene_tag_id': 40,
            'style_tag_id': 50,
        }
    ]

    result = MatchingService()._group_matching_rows(rows, {'sceneTagId': 40})

    assert result == [
        {
            'matchingId': 1,
            'matchingName': '通勤套装',
            'matchingTagId': 2,
            'matchingEOList': [
                {
                    'matchingId': 1,
                    'matchingName': '通勤套装',
                    'matchingTagId': 2,
                    'matchingSkuId': 10,
                    'productId': 20,
                    'productColorId': 30,
                    'colorFrontImgUrl': 'https://example.com/front.png',
                    'sceneTagId': 40,
                    'styleTagId': 50,
                }
            ],
            'skuCount': 1,
            'SkuCount': 1,
        }
    ]
