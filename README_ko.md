# Jupyter Notebook Translator

AWS Bedrock을 활용하여 고품질 번역을 제공하는 Jupyter Notebook 번역 도구입니다. 설정에 따라 마크다운 셀의 텍스트만 번역하거나, 마크다운 셀의 텍스트와 코드 셀의 텍스트 및 주석까지 모두 번역합니다.

## 주요 기능

- 🔄 **마크다운 셀 번역**: 코드 셀은 그대로 유지하고 마크다운 셀만 번역
- 💬 **주석 번역**: 마크다운 내 코드 블록의 # 주석 번역
- 🚀 **배치 처리**: 여러 셀을 한 번에 번역하여 효율성 향상
- 🎨 **자연스러운 번역**: 직역이 아닌 자연스러운 번역 옵션
- 🌐 **다국어 지원**: 50개 이상의 언어 지원
- 🤖 **다양한 모델**: AWS Bedrock의 여러 LLM 모델 지원

## 예시

### 번역

<table>
<tr>
<td><img src="imgs/original-en.png" alt="English"/></td>
<td><img src="imgs/translated-ko.png" alt="Korean"/></td>
</tr>
<tr>
<td align="center"><em>Original (English)t</em></td>
<td align="center"><em>Translated to Korean</em></td>
</tr>
</table>

### Kiro MCP 예시

![kiro1](imgs/mcp-kiro.png)

## 설치

```bash
# 저장소 클론
git clone https://github.com/daekeun-ml/ipynb-translator.git
cd ipynb-translator

# uv가 설치되어 있지 않다면
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성은 uv가 자동으로 관리합니다
```

## 설정

1. AWS 자격 증명 설정:
```bash
aws configure
```

2. 환경 변수 설정 (선택사항):
```bash
cp .env.example .env
# .env 파일을 편집하여 설정 조정
```

## 사용법

### 기본 번역

```bash
# 한국어로 번역
uv run ipynb-translate translate notebook.ipynb

# 특정 언어로 번역
uv run ipynb-translate translate notebook.ipynb -l ja

# 출력 파일 지정
uv run ipynb-translate translate notebook.ipynb -o translated_notebook.ipynb
```

### URL에서 다운로드 후 번역

```bash
# GitHub URL에서 노트북 다운로드 후 한국어로 번역
uv run ipynb-translate translate-url https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/01-AgentCore-runtime/02-hosting-MCP-server/hosting_mcp_server.ipynb

# 특정 언어로 번역하고 원본 파일 유지
uv run ipynb-translate translate-url https://example.com/notebook.ipynb -l ja --keep-original

# 출력 파일 지정
uv run ipynb-translate translate-url https://example.com/notebook.ipynb -o my_translated_notebook.ipynb
```

### 디렉토리 경로 번역

```bash
# 디렉토리 내 모든 노트북 번역
uv run ipynb-translate translate-path ./notebooks

# 특정 언어로 번역
uv run ipynb-translate translate-path ./notebooks -l ja

# 출력 디렉토리 지정
uv run ipynb-translate translate-path ./notebooks -o ./translated_notebooks
```

### 고급 옵션

```bash
# 특정 모델 사용
uv run ipynb-translate translate samples/notebook.ipynb -m cohere.command-r-plus-v1:0

# 배치 크기 조정
uv run ipynb-translate translate notebook.ipynb -b 10

# 번역 미리보기
uv run ipynb-translate translate notebook.ipynb --preview
```

### 유틸리티 명령어

```bash
# 노트북 정보 확인
uv run ipynb-translate info notebook.ipynb

# 지원 언어 목록
uv run ipynb-translate list-languages

# 지원 모델 목록
uv run ipynb-translate list-models

# AWS 자격 증명 확인
uv run ipynb-translate check-credentials
```

## 지원 언어

주요 지원 언어:
- 한국어 (ko)
- 일본어 (ja)
- 중국어 간체 (zh-CN)
- 중국어 번체 (zh-TW)
- 영어 (en)
- 프랑스어 (fr)
- 독일어 (de)
- 스페인어 (es)
- 이탈리아어 (it)
- 포르투갈어 (pt)
- 러시아어 (ru)
- 아랍어 (ar)
- 힌디어 (hi)
- 태국어 (th)
- 베트남어 (vi)

전체 목록: `uv run ipynb-translate list-languages`

## 지원 모델

- Amazon Nova (nova-micro, nova-lite, nova-pro, nova-premier)
- Anthropic Claude (3.5 Sonnet, 3.5 Haiku, 3.7 Sonnet, 4 Sonnet, 4 Opus)
- Meta Llama 3 (8B, 70B) / Llama 3.1 (8B, 70B, 405B) / Llama 3.2 (1B, 3B, 11B, 90B) / Llama 3.3 (70B)
- Meta Llama 4 (Scout 17B, Maverick 17B)
- DeepSeek R1
- Mistral (7B, 8x7B, Large)
- Cohere Command R/R+

전체 목록: `uv run ipynb-translate list-models`

## 설정 옵션

`.env` 파일에서 다음 설정을 조정할 수 있습니다:

```bash
# AWS 설정
AWS_REGION=us-east-1
AWS_PROFILE=default

# 번역 설정
DEFAULT_TARGET_LANGUAGE=ko
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
MAX_TOKENS=2000
TEMPERATURE=0.1
ENABLE_POLISHING=true          # 자연스러운 번역 활성화
TRANSLATE_CODE_CELLS=false     # 코드 셀 주석 번역 비활성화
BATCH_SIZE=5

# 디버그 설정
DEBUG=false
```

## MCP 제공 도구
FastMCP 서버는 다음 도구를 제공합니다:

### 1. translate_notebook
Jupyter 노트북을 지정된 언어로 번역합니다.

**매개변수:**
- `notebook_path` (필수): 노트북 파일 경로
- `target_language` (기본값: "ko"): 대상 언어 코드
- `output_path` (선택): 출력 파일 경로
- `model_id` (선택): Bedrock 모델 ID
- `batch_size` (기본값: 20): 배치 크기
- `translate_code_cells` (기본값: false): 코드 셀 주석 번역 여부
- `enable_polishing` (기본값: true): 자연스러운 번역 활성화

### 2. translate_from_url
URL에서 노트북을 다운로드하고 번역합니다.

**매개변수:**
- `url` (필수): 노트북 URL
- `target_language` (기본값: "ko"): 대상 언어 코드
- `output_path` (선택): 출력 파일 경로
- `keep_original` (기본값: false): 원본 파일 유지 여부
- `translate_code_cells` (기본값: false): 코드 셀 주석 번역 여부
- `enable_polishing` (기본값: true): 자연스러운 번역 활성화

### 3. get_notebook_info
노트북 파일 정보를 조회합니다.

### 4. list_supported_languages
지원되는 언어 목록을 반환합니다.

## MCP 설정 예시

```json
{
  "mcpServers": {
    "ipynb-translator": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "/path/to/ipynb-translator",
      "env": {
        "AWS_REGION": "us-east-1",
        "DEFAULT_TARGET_LANGUAGE": "ko",
        "BEDROCK_MODEL_ID": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "BATCH_SIZE": "5",
        "ENABLE_POLISHING": "true",
        "TRANSLATE_CODE_CELLS": "false",
        "TEMPERATURE": "0.1",
        "MAX_TOKENS": "2000"
      }
    }
  }
}
```

## 제한사항

- 매우 짧은 텍스트나 기술적 용어는 번역하지 않을 수 있음
- AWS Bedrock 사용량에 따른 비용 발생
- 인터넷 연결 필요

## 문제 해결

### AWS 자격 증명 오류
```bash
# AWS CLI 설정 확인
aws configure list

# 자격 증명 테스트
uv run ipynb-translate check-credentials
```

### 번역 품질 문제
- `.env` 파일에서 `ENABLE_POLISHING=true`로 설정하여 자연스러운 번역 활성화
- 다른 모델 시도 (`-m` 옵션)
- 배치 크기 조정 (`-b` 옵션)

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.