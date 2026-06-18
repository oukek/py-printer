#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指纹识别模块
提供 ZKFP 指纹设备相关的 API 接口
"""

import json

from flask import Blueprint, Response, jsonify, request, stream_with_context

from utils.fingerprint_utils import fingerprint_service


fingerprint_bp = Blueprint('fingerprint', __name__)


def _json_data():
    return request.get_json(silent=True) or {}


def _result_response(result, success_status=200, failure_status=500):
    status = success_status if result.get("success") else failure_status
    return jsonify(result), status


def _sse_event(event, payload):
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


def _query_int(name, default):
    value = request.args.get(name)
    if value is None:
        return default
    return int(value)


def _body_int(data, snake_name, camel_name, default):
    value = data.get(snake_name, data.get(camel_name, default))
    return int(value)


def _body_bool(data, snake_name, camel_name, default=False):
    value = data.get(snake_name, data.get(camel_name, default))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


@fingerprint_bp.route('/test', methods=['GET'])
def test_fingerprint():
    """测试指纹模块"""
    result = fingerprint_service.call("ping", message="指纹模块运行正常")
    if result.get("success"):
        result["endpoints"] = {
            "/fingerprint/device/count": "获取设备数量 (GET)",
            "/fingerprint/device/status": "获取设备打开状态 (GET)",
            "/fingerprint/device/open": "打开设备 (POST)",
            "/fingerprint/device/close": "关闭设备 (POST)",
            "/fingerprint/capture": "采集指纹 (POST)",
            "/fingerprint/enroll": "录入指纹 (POST)",
            "/fingerprint/enroll/events": "流式录入指纹 (GET, SSE)",
            "/fingerprint/identify": "识别指纹 (POST)",
            "/fingerprint/match": "比对两个指纹模板 (POST)",
            "/fingerprint/templates/add": "添加模板到内存库 (POST)",
            "/fingerprint/templates/load": "批量加载模板到内存库 (POST)",
            "/fingerprint/templates/delete": "删除内存库模板 (POST)",
            "/fingerprint/templates/clear": "清空内存库模板 (POST)",
            "/fingerprint/light": "控制设备灯光 (POST)",
        }
    return _result_response(result)


@fingerprint_bp.route('/device/count', methods=['GET'])
def get_device_count():
    """获取连接的指纹设备数量"""
    result = fingerprint_service.call("device_count", message="获取指纹设备数量成功")
    return _result_response(result)


@fingerprint_bp.route('/device/status', methods=['GET'])
def get_device_status():
    """获取当前指纹设备打开状态"""
    result = fingerprint_service.status()
    return _result_response(result)


@fingerprint_bp.route('/device/open', methods=['POST'])
def open_device():
    """
    打开指纹设备
    参数:
        index: 设备索引，默认 0
    """
    data = _json_data()
    result = fingerprint_service.call(
        "open",
        {"index": data.get("index", 0)},
        message="指纹设备打开成功"
    )
    return _result_response(result)


@fingerprint_bp.route('/device/close', methods=['POST'])
def close_device():
    """关闭指纹设备"""
    result = fingerprint_service.close()
    return _result_response(result)


@fingerprint_bp.route('/capture', methods=['POST'])
def capture_fingerprint():
    """
    采集一次指纹
    参数:
        timeout_ms / timeoutMs: 等待超时时间，默认 10000
    """
    data = _json_data()
    timeout_ms = data.get("timeout_ms", data.get("timeoutMs", 10000))
    result = fingerprint_service.call(
        "capture",
        {"timeoutMs": timeout_ms},
        message="指纹采集成功"
    )
    return _result_response(result, failure_status=408 if result.get("type") == "TimeoutError" else 500)


@fingerprint_bp.route('/enroll', methods=['POST'])
def enroll_fingerprint():
    """
    录入指纹，默认采集 3 次并合并模板
    参数:
        fid: 可选，指定模板 ID，提供后会加入内存识别库
        sample_count / sampleCount: 采样次数，ZKFP2 固定要求为 3
        timeout_ms / timeoutMs: 每次采集超时时间，默认 10000
    """
    data = _json_data()
    result = fingerprint_service.call(
        "enroll",
        {
            "fid": data.get("fid"),
            "sampleCount": data.get("sample_count", data.get("sampleCount", 3)),
            "timeoutMs": data.get("timeout_ms", data.get("timeoutMs", 10000)),
        },
        message="指纹录入成功"
    )
    return _result_response(result, failure_status=408 if result.get("type") == "TimeoutError" else 500)


@fingerprint_bp.route('/enroll/events', methods=['GET'])
def enroll_fingerprint_events():
    """
    SSE 流式录入指纹，每采集成功一次推送 captured 事件，完成后推送 completed 事件。
    查询参数:
        fid: 可选，指定模板 ID，提供后会加入内存识别库
        sample_count / sampleCount: 采样次数，ZKFP2 固定要求为 3
        timeout_ms / timeoutMs: 每次采集超时时间，默认 10000
    """
    try:
        fid_value = request.args.get("fid")
        fid = int(fid_value) if fid_value not in (None, "") else None
        sample_count = _query_int("sample_count", _query_int("sampleCount", 3))
        timeout_ms = _query_int("timeout_ms", _query_int("timeoutMs", 10000))
    except ValueError:
        return jsonify({
            "success": False,
            "error": "参数格式错误",
            "message": "fid、sample_count、timeout_ms 必须是整数"
        }), 400

    @stream_with_context
    def generate():
        try:
            yield _sse_event("started", {
                "success": True,
                "fid": fid,
                "total": sample_count,
                "timeoutMs": timeout_ms,
            })

            for event_data in fingerprint_service.enroll_events(
                fid=fid,
                sample_count=sample_count,
                timeout_ms=timeout_ms,
            ):
                if "step" in event_data:
                    yield _sse_event("captured", {
                        "success": True,
                        **event_data,
                    })
                else:
                    yield _sse_event("completed", {
                        "success": True,
                        "message": "指纹录入成功",
                        **event_data,
                    })
        except Exception as exc:
            yield _sse_event("error", {
                "success": False,
                "error": "指纹录入失败",
                "message": str(exc),
                "type": exc.__class__.__name__,
            })

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@fingerprint_bp.route('/identify', methods=['POST'])
def identify_fingerprint():
    """
    1:N 识别指纹
    参数:
        template_base64 / templateBase64: 可选，指定模板；不传则现场采集
        timeout_ms / timeoutMs: 现场采集超时时间，默认 10000
    """
    data = _json_data()
    try:
        timeout_ms = _body_int(data, "timeout_ms", "timeoutMs", 10000)
        min_score = _body_int(data, "min_score", "minScore", 1)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "参数格式错误",
            "message": "timeout_ms 和 min_score 必须是整数"
        }), 400

    params = {"timeoutMs": timeout_ms}
    template_base64 = data.get("template_base64", data.get("templateBase64"))
    if template_base64:
        params["templateBase64"] = template_base64

    result = fingerprint_service.call("identify", params, message="指纹识别完成")
    if result.get("success") and isinstance(result.get("result"), dict):
        identify_result = result["result"]
        fid = int(identify_result.get("fid") or 0)
        score = int(identify_result.get("score") or 0)
        identify_result["matched"] = fid > 0 and score >= min_score
        identify_result["minScore"] = min_score
        identify_result["timeoutMs"] = timeout_ms

    return _result_response(result, failure_status=408 if result.get("type") == "TimeoutError" else 500)


@fingerprint_bp.route('/match', methods=['POST'])
def match_fingerprints():
    """
    1:1 比对两个指纹模板
    参数:
        template1_base64 / template1Base64
        template2_base64 / template2Base64
    """
    data = _json_data()
    template1 = data.get("template1_base64", data.get("template1Base64"))
    template2 = data.get("template2_base64", data.get("template2Base64"))

    if not template1 or not template2:
        return jsonify({
            "success": False,
            "error": "缺少模板参数",
            "message": "template1_base64 和 template2_base64 均为必填"
        }), 400

    result = fingerprint_service.call(
        "match",
        {
            "template1Base64": template1,
            "template2Base64": template2,
        },
        message="指纹比对完成"
    )
    return _result_response(result)


@fingerprint_bp.route('/templates/add', methods=['POST'])
def add_template():
    """
    添加指纹模板到内存识别库
    参数:
        fid: 模板 ID
        template_base64 / templateBase64: 指纹模板
    """
    data = _json_data()
    fid = data.get("fid")
    template_base64 = data.get("template_base64", data.get("templateBase64"))

    if fid is None or not template_base64:
        return jsonify({
            "success": False,
            "error": "缺少模板参数",
            "message": "fid 和 template_base64 均为必填"
        }), 400

    result = fingerprint_service.call(
        "add_template",
        {
            "fid": fid,
            "templateBase64": template_base64,
        },
        message="指纹模板添加成功"
    )
    return _result_response(result)


@fingerprint_bp.route('/templates/load', methods=['POST'])
def load_templates():
    """
    批量加载业务库中的指纹模板到 SDK 内存识别库
    参数:
        templates: [{ fid, template_base64/templateBase64 }]
        clear_existing / clearExisting: 是否先清空内存库，默认 False
    """
    data = _json_data()
    templates = data.get("templates")
    clear_existing = _body_bool(data, "clear_existing", "clearExisting", False)

    if not isinstance(templates, list):
        return jsonify({
            "success": False,
            "error": "缺少templates参数",
            "message": "templates 必须是数组"
        }), 400

    result = fingerprint_service.load_templates(templates, clear_existing)
    return _result_response(result)


@fingerprint_bp.route('/templates/delete', methods=['POST'])
def delete_template():
    """
    删除内存识别库中的指纹模板
    参数:
        fid: 模板 ID
    """
    data = _json_data()
    fid = data.get("fid")

    if fid is None:
        return jsonify({
            "success": False,
            "error": "缺少fid参数",
            "message": "fid 为必填"
        }), 400

    result = fingerprint_service.call(
        "delete_template",
        {"fid": fid},
        message="指纹模板删除成功"
    )
    return _result_response(result)


@fingerprint_bp.route('/templates/clear', methods=['POST'])
def clear_templates():
    """清空内存识别库中的指纹模板"""
    result = fingerprint_service.call("clear_templates", message="指纹模板已清空")
    return _result_response(result)


@fingerprint_bp.route('/templates/merge', methods=['POST'])
def merge_templates():
    """
    合并 3 个预登记模板
    参数:
        templates_base64 / templatesBase64: 长度为 3 的模板数组
        fid: 可选，指定后会加入内存识别库
    """
    data = _json_data()
    templates = data.get("templates_base64", data.get("templatesBase64"))

    if not isinstance(templates, list) or len(templates) != 3:
        return jsonify({
            "success": False,
            "error": "模板数量错误",
            "message": "templates_base64 必须是长度为 3 的数组"
        }), 400

    result = fingerprint_service.call(
        "merge_templates",
        {
            "templatesBase64": templates,
            "fid": data.get("fid"),
        },
        message="指纹模板合并成功"
    )
    return _result_response(result)


@fingerprint_bp.route('/light', methods=['POST'])
def set_light():
    """
    控制指纹设备灯光
    参数:
        color: white / green / red，默认 green
        duration: 持续时间秒，默认 0.5
    """
    data = _json_data()
    result = fingerprint_service.call(
        "light",
        {
            "color": data.get("color", "green"),
            "duration": data.get("duration", 0.5),
        },
        message="指纹设备灯光控制成功"
    )
    return _result_response(result)
