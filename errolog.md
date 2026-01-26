🔍 Coleta e Processamento
succeeded 1 minute ago in 50s
Search logs
1s
Current runner version: '2.331.0'
Runner Image Provisioner
Operating System
Runner Image
GITHUB_TOKEN Permissions
Secret source: Actions
Prepare workflow directory
Prepare all required actions
Getting action download info
Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
Download action repository 'actions/setup-python@v5' (SHA:a26af69be951a213d495a4c3e4e4022e16d87065)
Download action repository 'actions/cache@v4' (SHA:0057852bfaa89a56745cba8c7296529d2fc39830)
Download action repository 'actions/upload-artifact@v4' (SHA:ea165f8d65b6e75b540449e92b4886f43607fa02)
Complete job name: 🔍 Coleta e Processamento
1s
Run actions/checkout@v4
Syncing repository: diegosantos-ai/pega-vagas
Getting Git version info
Temporarily overriding HOME='/home/runner/work/_temp/31e8b4a6-0fe0-4b29-b505-238482759ee6' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/pega-vagas/pega-vagas
Deleting the contents of '/home/runner/work/pega-vagas/pega-vagas'
Initializing the repository
Disabling automatic garbage collection
Setting up auth
Fetching the repository
Determining the checkout info
/usr/bin/git sparse-checkout disable
/usr/bin/git config --local --unset-all extensions.worktreeConfig
Checking out the ref
/usr/bin/git log -1 --format=%H
159a3c7b51d5d4e4237fdcc8c18f3ae7eb644538
4s
Run actions/setup-python@v5
Installed versions
/opt/hostedtoolcache/Python/3.11.14/x64/bin/pip cache dir
/home/runner/.cache/pip
Cache hit for: setup-python-Linux-x64-24.04-Ubuntu-python-3.11.14-pip-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
Received 50331648 of 301168104 (16.7%), 48.0 MBs/sec
Received 222298112 of 301168104 (73.8%), 106.0 MBs/sec
Received 301168104 of 301168104 (100.0%), 115.6 MBs/sec
Cache Size: ~287 MB (301168104 B)
/usr/bin/tar -xf /home/runner/work/_temp/0c20f4e0-6066-40f0-8166-9403e507e71f/cache.tzst -P -C /home/runner/work/pega-vagas/pega-vagas --use-compress-program unzstd
Cache restored successfully
Cache restored from key: setup-python-Linux-x64-24.04-Ubuntu-python-3.11.14-pip-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
4s
Run actions/cache@v4
  
Cache hit for: pip-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
Received 58720256 of 301169260 (19.5%), 55.9 MBs/sec
Received 213909504 of 301169260 (71.0%), 101.9 MBs/sec
Received 301169260 of 301169260 (100.0%), 109.6 MBs/sec
Cache Size: ~287 MB (301169260 B)
/usr/bin/tar -xf /home/runner/work/_temp/07b37d4b-391f-4d50-a330-9188afe55944/cache.tzst -P -C /home/runner/work/pega-vagas/pega-vagas --use-compress-program unzstd
Cache restored successfully
Cache restored from key: pip-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
2s
Run actions/cache@v4
  
Cache hit for: playwright-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
Received 58720256 of 99680057 (58.9%), 55.9 MBs/sec
Received 99680057 of 99680057 (100.0%), 74.7 MBs/sec
Cache Size: ~95 MB (99680057 B)
/usr/bin/tar -xf /home/runner/work/_temp/0b1cb5ce-77f1-428b-b3b3-8d7f4fb36e70/cache.tzst -P -C /home/runner/work/pega-vagas/pega-vagas --use-compress-program unzstd
Cache restored successfully
Cache restored from key: playwright-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5
0s
Run actions/cache@v4
  
Cache not found for input keys: seen-jobs-21374516623, seen-jobs-
0s
Run echo "Cache hit: "
Cache hit: 
total 20
drwxr-xr-x 4 runner runner 4096 Jan 26 20:21 .
drwxr-xr-x 8 runner runner 4096 Jan 26 20:21 ..
-rw-r--r-- 1 runner runner  318 Jan 26 20:21 .seen_jobs_test.json
drwxr-xr-x 3 runner runner 4096 Jan 26 20:21 gold
drwxr-xr-x 2 runner runner 4096 Jan 26 20:21 jobs
⚠️ Cache não encontrado ou arquivo ausente
24s
Run python -m pip install --upgrade pip
  
Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (25.3)
Obtaining file:///home/runner/work/pega-vagas/pega-vagas
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Installing backend dependencies: started
  Installing backend dependencies: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Collecting beautifulsoup4>=4.12.0 (from pega-vagas==0.1.0)
  Using cached beautifulsoup4-4.14.3-py3-none-any.whl.metadata (3.8 kB)
Collecting camoufox>=0.4.0 (from pega-vagas==0.1.0)
  Using cached camoufox-0.4.11-py3-none-any.whl.metadata (3.3 kB)
Collecting duckdb>=1.1.0 (from pega-vagas==0.1.0)
  Using cached duckdb-1.4.4-cp311-cp311-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (4.3 kB)
Collecting google-genai>=1.0.0 (from pega-vagas==0.1.0)
  Using cached google_genai-1.60.0-py3-none-any.whl.metadata (53 kB)
Collecting httpx>=0.27.0 (from pega-vagas==0.1.0)
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting openai>=1.50.0 (from pega-vagas==0.1.0)
  Using cached openai-2.15.0-py3-none-any.whl.metadata (29 kB)
Collecting pandas>=2.2.0 (from pega-vagas==0.1.0)
  Using cached pandas-3.0.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (79 kB)
Collecting playwright>=1.40.0 (from pega-vagas==0.1.0)
  Using cached playwright-1.57.0-py3-none-manylinux1_x86_64.whl.metadata (3.5 kB)
Collecting pyarrow>=18.0.0 (from pega-vagas==0.1.0)
  Using cached pyarrow-23.0.0-cp311-cp311-manylinux_2_28_x86_64.whl.metadata (3.0 kB)
Collecting pydantic>=2.9.0 (from pega-vagas==0.1.0)
  Using cached pydantic-2.12.5-py3-none-any.whl.metadata (90 kB)
Collecting python-dotenv>=1.0.0 (from pega-vagas==0.1.0)
  Using cached python_dotenv-1.2.1-py3-none-any.whl.metadata (25 kB)
Collecting rich>=13.0.0 (from pega-vagas==0.1.0)
  Using cached rich-14.3.1-py3-none-any.whl.metadata (18 kB)
Collecting structlog>=24.0.0 (from pega-vagas==0.1.0)
  Using cached structlog-25.5.0-py3-none-any.whl.metadata (9.5 kB)
Collecting tenacity>=9.0.0 (from pega-vagas==0.1.0)
  Using cached tenacity-9.1.2-py3-none-any.whl.metadata (1.2 kB)
Collecting trafilatura>=1.12.0 (from pega-vagas==0.1.0)
  Using cached trafilatura-2.0.0-py3-none-any.whl.metadata (12 kB)
Collecting mypy>=1.11.0 (from pega-vagas==0.1.0)
  Using cached mypy-1.19.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.2 kB)
Collecting pytest-asyncio>=0.24.0 (from pega-vagas==0.1.0)
  Using cached pytest_asyncio-1.3.0-py3-none-any.whl.metadata (4.1 kB)
Collecting pytest>=8.0.0 (from pega-vagas==0.1.0)
  Using cached pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
Collecting ruff>=0.6.0 (from pega-vagas==0.1.0)
  Using cached ruff-0.14.14-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (26 kB)
Collecting soupsieve>=1.6.1 (from beautifulsoup4>=4.12.0->pega-vagas==0.1.0)
  Using cached soupsieve-2.8.3-py3-none-any.whl.metadata (4.6 kB)
Collecting typing-extensions>=4.0.0 (from beautifulsoup4>=4.12.0->pega-vagas==0.1.0)
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting browserforge<2.0.0,>=1.2.1 (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached browserforge-1.2.3-py3-none-any.whl.metadata (28 kB)
Collecting click (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
Collecting language-tags (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached language_tags-1.2.0-py3-none-any.whl.metadata (2.1 kB)
Collecting lxml (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached lxml-6.0.2-cp311-cp311-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (3.6 kB)
Collecting numpy (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached numpy-2.4.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
Collecting orjson (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached orjson-3.11.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (41 kB)
Collecting platformdirs (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached platformdirs-4.5.1-py3-none-any.whl.metadata (12 kB)
Collecting pysocks (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached PySocks-1.7.1-py3-none-any.whl.metadata (13 kB)
Collecting pyyaml (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
Collecting requests (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached requests-2.32.5-py3-none-any.whl.metadata (4.9 kB)
Collecting screeninfo (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached screeninfo-0.8.1-py3-none-any.whl.metadata (2.9 kB)
Collecting tqdm (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached tqdm-4.67.1-py3-none-any.whl.metadata (57 kB)
Collecting ua_parser (from camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached ua_parser-1.0.1-py3-none-any.whl.metadata (5.6 kB)
Collecting anyio<5.0.0,>=4.8.0 (from google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached anyio-4.12.1-py3-none-any.whl.metadata (4.3 kB)
Collecting google-auth<3.0.0,>=2.47.0 (from google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached google_auth-2.48.0-py3-none-any.whl.metadata (6.2 kB)
Collecting websockets<15.1.0,>=13.0.0 (from google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting distro<2,>=1.7.0 (from google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached distro-1.9.0-py3-none-any.whl.metadata (6.8 kB)
Collecting sniffio (from google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting idna>=2.8 (from anyio<5.0.0,>=4.8.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting pyasn1-modules>=0.2.1 (from google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached pyasn1_modules-0.4.2-py3-none-any.whl.metadata (3.5 kB)
Collecting cryptography>=38.0.3 (from google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl.metadata (5.7 kB)
Collecting rsa<5,>=3.1.4 (from google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached rsa-4.9.1-py3-none-any.whl.metadata (5.6 kB)
Collecting certifi (from httpx>=0.27.0->pega-vagas==0.1.0)
  Using cached certifi-2026.1.4-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx>=0.27.0->pega-vagas==0.1.0)
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx>=0.27.0->pega-vagas==0.1.0)
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->pega-vagas==0.1.0)
  Using cached annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.41.5 (from pydantic>=2.9.0->pega-vagas==0.1.0)
  Using cached pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.3 kB)
Collecting typing-inspection>=0.4.2 (from pydantic>=2.9.0->pega-vagas==0.1.0)
  Using cached typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting charset_normalizer<4,>=2 (from requests->camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (37 kB)
Collecting urllib3<3,>=1.21.1 (from requests->camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
Collecting pyasn1>=0.1.3 (from rsa<5,>=3.1.4->google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached pyasn1-0.6.2-py3-none-any.whl.metadata (8.4 kB)
Collecting cffi>=2.0.0 (from cryptography>=38.0.3->google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=2.0.0->cryptography>=38.0.3->google-auth<3.0.0,>=2.47.0->google-auth[requests]<3.0.0,>=2.47.0->google-genai>=1.0.0->pega-vagas==0.1.0)
  Using cached pycparser-3.0-py3-none-any.whl.metadata (8.2 kB)
Collecting mypy_extensions>=1.0.0 (from mypy>=1.11.0->pega-vagas==0.1.0)
  Using cached mypy_extensions-1.1.0-py3-none-any.whl.metadata (1.1 kB)
Collecting pathspec>=0.9.0 (from mypy>=1.11.0->pega-vagas==0.1.0)
  Using cached pathspec-1.0.3-py3-none-any.whl.metadata (13 kB)
Collecting librt>=0.6.2 (from mypy>=1.11.0->pega-vagas==0.1.0)
  Using cached librt-0.7.8-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (1.3 kB)
Collecting jiter<1,>=0.10.0 (from openai>=1.50.0->pega-vagas==0.1.0)
  Using cached jiter-0.12.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.2 kB)
Collecting python-dateutil>=2.8.2 (from pandas>=2.2.0->pega-vagas==0.1.0)
  Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting pyee<14,>=13 (from playwright>=1.40.0->pega-vagas==0.1.0)
  Using cached pyee-13.0.0-py3-none-any.whl.metadata (2.9 kB)
Collecting greenlet<4.0.0,>=3.1.1 (from playwright>=1.40.0->pega-vagas==0.1.0)
  Using cached greenlet-3.3.1-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (3.7 kB)
Collecting iniconfig>=1.0.1 (from pytest>=8.0.0->pega-vagas==0.1.0)
  Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
Collecting packaging>=22 (from pytest>=8.0.0->pega-vagas==0.1.0)
  Using cached packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
Collecting pluggy<2,>=1.5 (from pytest>=8.0.0->pega-vagas==0.1.0)
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pygments>=2.7.2 (from pytest>=8.0.0->pega-vagas==0.1.0)
  Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
Collecting six>=1.5 (from python-dateutil>=2.8.2->pandas>=2.2.0->pega-vagas==0.1.0)
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.0.0->pega-vagas==0.1.0)
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.0.0->pega-vagas==0.1.0)
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting courlan>=1.3.2 (from trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached courlan-1.3.2-py3-none-any.whl.metadata (17 kB)
Collecting htmldate>=1.9.2 (from trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached htmldate-1.9.4-py3-none-any.whl.metadata (10 kB)
Collecting justext>=3.0.1 (from trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached justext-3.0.2-py2.py3-none-any.whl.metadata (7.3 kB)
Collecting babel>=2.16.0 (from courlan>=1.3.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached babel-2.17.0-py3-none-any.whl.metadata (2.0 kB)
Collecting tld>=0.13 (from courlan>=1.3.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached tld-0.13.1-py2.py3-none-any.whl.metadata (10 kB)
Collecting dateparser>=1.1.2 (from htmldate>=1.9.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached dateparser-1.2.2-py3-none-any.whl.metadata (29 kB)
Collecting pytz>=2024.2 (from dateparser>=1.1.2->htmldate>=1.9.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached pytz-2025.2-py2.py3-none-any.whl.metadata (22 kB)
Collecting regex>=2024.9.11 (from dateparser>=1.1.2->htmldate>=1.9.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached regex-2026.1.15-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
Collecting tzlocal>=0.2 (from dateparser>=1.1.2->htmldate>=1.9.2->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached tzlocal-5.3.1-py3-none-any.whl.metadata (7.6 kB)
Collecting lxml_html_clean (from lxml[html_clean]>=4.4.2->justext>=3.0.1->trafilatura>=1.12.0->pega-vagas==0.1.0)
  Using cached lxml_html_clean-0.4.3-py3-none-any.whl.metadata (2.3 kB)
Collecting ua-parser-builtins (from ua_parser->camoufox>=0.4.0->pega-vagas==0.1.0)
  Using cached ua_parser_builtins-202601-py3-none-any.whl.metadata (1.6 kB)
Using cached beautifulsoup4-4.14.3-py3-none-any.whl (107 kB)
Using cached camoufox-0.4.11-py3-none-any.whl (71 kB)
Using cached browserforge-1.2.3-py3-none-any.whl (39 kB)
Using cached duckdb-1.4.4-cp311-cp311-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (20.4 MB)
Using cached google_genai-1.60.0-py3-none-any.whl (719 kB)
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Using cached distro-1.9.0-py3-none-any.whl (20 kB)
Using cached google_auth-2.48.0-py3-none-any.whl (236 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached pydantic-2.12.5-py3-none-any.whl (463 kB)
Using cached pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached rsa-4.9.1-py3-none-any.whl (34 kB)
Using cached tenacity-9.1.2-py3-none-any.whl (28 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached urllib3-2.6.3-py3-none-any.whl (131 kB)
Using cached websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached certifi-2026.1.4-py3-none-any.whl (152 kB)
Using cached cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl (4.5 MB)
Using cached cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached mypy-1.19.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (13.4 MB)
Using cached librt-0.7.8-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (188 kB)
Using cached mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Using cached openai-2.15.0-py3-none-any.whl (1.1 MB)
Using cached jiter-0.12.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (364 kB)
Using cached pandas-3.0.0-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (11.2 MB)
Using cached numpy-2.4.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.7 MB)
Using cached pathspec-1.0.3-py3-none-any.whl (55 kB)
Using cached playwright-1.57.0-py3-none-manylinux1_x86_64.whl (46.0 MB)
Using cached greenlet-3.3.1-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (590 kB)
Using cached pyee-13.0.0-py3-none-any.whl (15 kB)
Using cached pyarrow-23.0.0-cp311-cp311-manylinux_2_28_x86_64.whl (47.5 MB)
Using cached pyasn1-0.6.2-py3-none-any.whl (83 kB)
Using cached pyasn1_modules-0.4.2-py3-none-any.whl (181 kB)
Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached packaging-26.0-py3-none-any.whl (74 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytest_asyncio-1.3.0-py3-none-any.whl (15 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached python_dotenv-1.2.1-py3-none-any.whl (21 kB)
Using cached rich-14.3.1-py3-none-any.whl (309 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Using cached ruff-0.14.14-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (11.2 MB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached soupsieve-2.8.3-py3-none-any.whl (37 kB)
Using cached structlog-25.5.0-py3-none-any.whl (72 kB)
Using cached tqdm-4.67.1-py3-none-any.whl (78 kB)
Using cached trafilatura-2.0.0-py3-none-any.whl (132 kB)
Using cached courlan-1.3.2-py3-none-any.whl (33 kB)
Using cached babel-2.17.0-py3-none-any.whl (10.2 MB)
Using cached htmldate-1.9.4-py3-none-any.whl (31 kB)
Using cached dateparser-1.2.2-py3-none-any.whl (315 kB)
Using cached justext-3.0.2-py2.py3-none-any.whl (837 kB)
Using cached lxml-6.0.2-cp311-cp311-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (5.2 MB)
Using cached pytz-2025.2-py2.py3-none-any.whl (509 kB)
Using cached regex-2026.1.15-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (800 kB)
Using cached tld-0.13.1-py2.py3-none-any.whl (274 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached tzlocal-5.3.1-py3-none-any.whl (18 kB)
Using cached click-8.3.1-py3-none-any.whl (108 kB)
Using cached language_tags-1.2.0-py3-none-any.whl (213 kB)
Using cached lxml_html_clean-0.4.3-py3-none-any.whl (14 kB)
Using cached orjson-3.11.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (138 kB)
Using cached platformdirs-4.5.1-py3-none-any.whl (18 kB)
Using cached pycparser-3.0-py3-none-any.whl (48 kB)
Using cached PySocks-1.7.1-py3-none-any.whl (16 kB)
Using cached pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (806 kB)
Using cached screeninfo-0.8.1-py3-none-any.whl (12 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached ua_parser-1.0.1-py3-none-any.whl (31 kB)
Using cached ua_parser_builtins-202601-py3-none-any.whl (89 kB)
Building wheels for collected packages: pega-vagas
  Building editable for pega-vagas (pyproject.toml): started
  Building editable for pega-vagas (pyproject.toml): finished with status 'done'
  Created wheel for pega-vagas: filename=pega_vagas-0.1.0-py3-none-any.whl size=4203 sha256=899de9f539f432a01737989043685f457c210f5d2a563787ab8106412b565c17
  Stored in directory: /tmp/pip-ephem-wheel-cache-zwnd0xu4/wheels/bb/0d/75/0e2bcd61b425195d3ece393f28dedf804516b13d1dbdda6da9
Successfully built pega-vagas
Installing collected packages: pytz, language-tags, websockets, urllib3, ua-parser-builtins, tzlocal, typing-extensions, tqdm, tld, tenacity, structlog, soupsieve, sniffio, six, screeninfo, ruff, regex, pyyaml, python-dotenv, pysocks, pygments, pycparser, pyasn1, pyarrow, pluggy, platformdirs, pathspec, packaging, orjson, numpy, mypy_extensions, mdurl, lxml, librt, jiter, iniconfig, idna, h11, greenlet, duckdb, distro, click, charset_normalizer, certifi, babel, annotated-types, ua_parser, typing-inspection, rsa, requests, python-dateutil, pytest, pyee, pydantic-core, pyasn1-modules, mypy, markdown-it-py, lxml_html_clean, httpcore, courlan, cffi, browserforge, beautifulsoup4, anyio, rich, pytest-asyncio, pydantic, playwright, pandas, httpx, dateparser, cryptography, openai, justext, htmldate, google-auth, camoufox, trafilatura, google-genai, pega-vagas
Successfully installed annotated-types-0.7.0 anyio-4.12.1 babel-2.17.0 beautifulsoup4-4.14.3 browserforge-1.2.3 camoufox-0.4.11 certifi-2026.1.4 cffi-2.0.0 charset_normalizer-3.4.4 click-8.3.1 courlan-1.3.2 cryptography-46.0.3 dateparser-1.2.2 distro-1.9.0 duckdb-1.4.4 google-auth-2.48.0 google-genai-1.60.0 greenlet-3.3.1 h11-0.16.0 htmldate-1.9.4 httpcore-1.0.9 httpx-0.28.1 idna-3.11 iniconfig-2.3.0 jiter-0.12.0 justext-3.0.2 language-tags-1.2.0 librt-0.7.8 lxml-6.0.2 lxml_html_clean-0.4.3 markdown-it-py-4.0.0 mdurl-0.1.2 mypy-1.19.1 mypy_extensions-1.1.0 numpy-2.4.1 openai-2.15.0 orjson-3.11.5 packaging-26.0 pandas-3.0.0 pathspec-1.0.3 pega-vagas-0.1.0 platformdirs-4.5.1 playwright-1.57.0 pluggy-1.6.0 pyarrow-23.0.0 pyasn1-0.6.2 pyasn1-modules-0.4.2 pycparser-3.0 pydantic-2.12.5 pydantic-core-2.41.5 pyee-13.0.0 pygments-2.19.2 pysocks-1.7.1 pytest-9.0.2 pytest-asyncio-1.3.0 python-dateutil-2.9.0.post0 python-dotenv-1.2.1 pytz-2025.2 pyyaml-6.0.3 regex-2026.1.15 requests-2.32.5 rich-14.3.1 rsa-4.9.1 ruff-0.1
Requirement already satisfied: pyyaml in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (6.0.3)
0s
Run echo "🔍 Verificando configuração..."
🔍 Verificando configuração...
✅ Configuração OK
4s
Run echo "📥 Iniciando coleta de vagas..."
📥 Iniciando coleta de vagas...
2026-01-26 20:22:21 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
2026-01-26T23:22:22.485000Z [error    ] [gupy] Erro: can't compare offset-naive and offset-aware datetimes
2026-01-26T23:22:22.656786Z [error    ] Erro fatal no scraper programathor: name 'urllib' is not defined
2026-01-26 20:22:22 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
2026-01-26T23:22:23.558965Z [error    ] Erro fatal no scraper programathor: name 'urllib' is not defined
2026-01-26 20:22:23 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
2026-01-26T23:22:24.366795Z [error    ] Erro fatal no scraper programathor: name 'urllib' is not defined
2026-01-26 20:22:24 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
2026-01-26T23:22:25.113897Z [error    ] [gupy] Erro: can't compare offset-naive and offset-aware datetimes
2026-01-26T23:22:25.239539Z [error    ] Erro fatal no scraper programathor: name 'urllib' is not defined
📊 Arquivos coletados:
0
1s
Run echo "🤖 Processando com LLM..."
🤖 Processando com LLM...
2026-01-26 20:22:25 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
📊 Arquivos processados:
0
0s
Run echo "💎 Gerando camada Gold..."
💎 Gerando camada Gold...
2026-01-26 20:22:26 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
1s
Run echo "📦 Exportando para Parquet..."
📦 Exportando para Parquet...
2026-01-26 20:22:27 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
0s
Run echo "📲 Enviando notificações..."
📲 Enviando notificações...
2026-01-26 20:22:27 [info     ] Configuração carregada de /home/runner/work/pega-vagas/pega-vagas/config.yaml
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/pega-vagas/pega-vagas/src/pipeline.py", line 353, in <module>
    main()
  File "/home/runner/work/pega-vagas/pega-vagas/src/pipeline.py", line 346, in main
    asyncio.run(run_notify())
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/runner/work/pega-vagas/pega-vagas/src/pipeline.py", line 218, in run_notify
    from src.notifications.telegram_v2 import TelegramNotifierV2
  File "/home/runner/work/pega-vagas/pega-vagas/src/notifications/__init__.py", line 5, in <module>
    from src.notifications.telegram import TelegramNotifier
  File "/home/runner/work/pega-vagas/pega-vagas/src/notifications/telegram.py", line 21, in <module>
    from src.config.settings import settings
  File "/home/runner/work/pega-vagas/pega-vagas/src/config/settings.py", line 4, in <module>
    from pydantic_settings import BaseSettings, SettingsConfigDict
ModuleNotFoundError: No module named 'pydantic_settings'
Error: Process completed with exit code 1.
0s
Run actions/cache/save@v4
Warning: Path Validation Error: Path(s) specified in the action for caching do(es) not exist, hence no cache is being saved.
Warning: Cache save failed.
0s
Run actions/upload-artifact@v4
No files were found with the provided path: data/bronze/. No artifacts will be uploaded.
0s
Run actions/upload-artifact@v4
No files were found with the provided path: data/silver/. No artifacts will be uploaded.
1s
Run actions/upload-artifact@v4
With the provided path, there will be 9 files uploaded
Artifact name is valid!
Root directory input is valid!
Beginning upload of artifact content to blob storage
Uploaded bytes 7356
Finished uploading artifact content to blob storage!
SHA256 digest of uploaded artifact zip is 5e2bc15f6f0ac6f9c18c76876c75ea62799e798dc0be1698f61cad5c0fc4f6c4
Finalizing artifact upload
Artifact gold-data-12.zip successfully finalized. Artifact ID 5264697736
Artifact gold-data-12 has been successfully uploaded! Final size is 7356 bytes. Artifact ID is 5264697736
Artifact download URL: https://github.com/diegosantos-ai/pega-vagas/actions/runs/21374516623/artifacts/5264697736
0s
0s
Run echo "## 📊 Pipeline Summary" >> $GITHUB_STEP_SUMMARY
0s
Post job cleanup.
Warning: Path Validation Error: Path(s) specified in the action for caching do(es) not exist, hence no cache is being saved.
1s
Post job cleanup.
Cache hit occurred on the primary key playwright-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5, not saving cache.
0s
Post job cleanup.
Cache hit occurred on the primary key pip-Linux-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5, not saving cache.
0s
Post job cleanup.
Cache hit occurred on the primary key setup-python-Linux-x64-24.04-Ubuntu-python-3.11.14-pip-19b81498a1b57730c82515a014411c4b94c1f3ad796a9cb7d557f65ebebf81e5, not saving cache.
0s
Post job cleanup.
/usr/bin/git version
git version 2.52.0
Temporarily overriding HOME='/home/runner/work/_temp/18d09d71-b86f-43db-958c-39a1939c0f94' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/pega-vagas/pega-vagas
/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
http.https://github.com/.extraheader
/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
