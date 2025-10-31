from openai import OpenAI
import os
import json

def gpt(response_format, label, src_url):
    client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,  # remove randomness
        
        # 3-shot: 데일리, 캠퍼스, 출근 (오버피팅될 수 있으므로 2-3 shot이 적당)
        messages=[{
            "role": "system",
            "content": '''너는 프로페셔널한 패션 디자이너야. 각 착장 이미지를 보고 상의, 하의, 신발, 가방의 색, 질감, 분위기를 문장이 아닌 명사로 묘사해. 
        또한 전체적인 착장의 TPO (시간, 장소, 상황)를 한 문장으로 요약해. 반환은 지정된 JSON 스키마에 맞춘 값만 포함하고 스키마 구조 자체는 포함하지 마.'''
        },
        {   
            "role": "user",
            "content": [
                # 1
                # {"type": "text", "text": "첫 번째 착장 이미지"},
                # {"type": "image_url", "image_url": {"url": "https://image.msscdn.net/thumbnails/snap/images/2025/01/30/d0011a48c2bc4cdd95183e9dce3ebfea.jpg?w=1000"}},
                # {"type": "text", "text": "상의: 블랙 기본티와 블랙 항공 점퍼\n하의: 흰색 스트레이트 바지\n가방: 없음\n신발: 블랙 플랫 슈즈\nTPO: 가을에 친구들과 편하게 놀 때 입는 데일리룩"},

                {"type": "text", "text": "첫 번째 착장 이미지"},
                {"type": "image_url", "image_url": {"url": "https://image.msscdn.net/thumbnails/images/style/detail/56144/detail_56144_68d548e8b433d_500.jpg?w=1000"}},
                {"type": "text", "text": "상의: 흰색 기본티, 회색 후드집업, 남색 야구점퍼\n하의: 모카색 와이드 핏 팬츠\n가방: 물방울 무늬 블랙 가방\n신발: 흰색 운동화\nTPO: 겨울에 데이트할 때 입는 힙하고 따뜻한 인싸룩"},  
                
                {"type": "text", "text": "두 번째 착장 이미지"},
                {"type": "image_url", "image_url": {"url": "https://image.msscdn.net/thumbnails/snap/images/2025/01/09/8aa9c17d21fc4e5a937c908048410361.jpg?w=1000"}},
                {"type": "text", "text": "상의: 카키색 목티, 갈색 코드\n하의: 검정 스트레이트 진\n가방: 없음\n신발: 검정 로퍼\nTPO: 겨울에 입기 좋은 단정하고 분위기 있는 오피스룩"},
                
                # 8
                {"type": "text", "text": f"세 번째 착장 이미지"},
                {"type": "image_url", "image_url": {"url": src_url}},
                {"type": "text", "text": f"위 두 가지 예시를 참고해 세 번째 착장 이미지에 대한 상의, 하의, 가방, 신발, TPO를 묘사해줘. TPO는 최대한 구체적으로 반환은 JSON 텍스트로만, 스키마의 키 (top, bottom, bag, shoes, TPO)만 사용해. items 배열에 label은 {label} 하나만 넣어."}
                
            ]
        }
        ],
        response_format = response_format        
    )
    print(response.choices[0].message.content)
    json_response = json.loads(response.choices[0].message.content)
    return json_response

def main():

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "fashion_extract",
            "schema": {
                "type": "object",
                "properties":{
                    "label": {"type": "string"},
                    "top": {"type": "string"},
                    "bottom": {"type": "string"},
                    "bag": {"type": "string"},
                    "shoes": {"type": "string"},
                    "TPO": {"type": "string"}
                },
                "required": ["label", "top", "bottom", "bag", "shoes", "TPO"],
                "additionalProperties": False,
            }}
        }
    
    results = []
    os.makedirs("json", exist_ok=True)
    filename = "snap_fashion_extract.json"
    save_path = os.path.join("/Users/minair/GetReadyWithChoi/json/snap_image", filename)
    
    with open("/Users/minair/GetReadyWithChoi/json/snap_image/snap_dedup.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for i, item in enumerate(data):
        label = item.get("index")
        tpo = item.get("TPO")
        src_url = item.get("src")
        json_response = gpt(response_format=response_format, label=label, src_url=src_url)
        results.append(json_response)
        if i >= 2: # 테스트
            break
    f.close()
            
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)    
    
if __name__ == "__main__":
    main()