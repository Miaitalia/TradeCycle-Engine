from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI(
    title="TradeCycle Engine",
    description="خوارزمية المطابقة الدائرية الذكية للمقايضة بدون نقود"
)

# السماح للواجهة الأمامية (Netlify) بالتواصل مع السيرفر دون قيود CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نمذج بيانات الرغبات والمنتجات
class SwapRequest(BaseModel):
    user_id: str
    offering: str  # الشرف الذي يمتلكه ويود التنازل عنه
    desiring: str  # الشيء الذي يبحث عنه ويرغب به

class CycleResponse(BaseModel):
    cycle_length: int
    chain: List[Dict[str, str]]

# قاعدة بيانات مؤقتة في الذاكرة لتخزين الطلبات
db_requests: List[SwapRequest] = [
    # بيانات أولية للتجربة (المحاكاة)
    SwapRequest(user_id="أحمد", offering="iPhone 13", desiring="PS5"),
    SwapRequest(user_id="سارة", offering="PS5", desiring="MacBook Pro"),
    SwapRequest(user_id="خالد", offering="MacBook Pro", desiring="iPhone 13"),
]

def find_cycles(requests: List[SwapRequest], max_depth: int = 5) -> List[List[SwapRequest]]:
    """
    خوارزمية البحث في العمق (Depth-First Search) لاكتشاف الحلقات المغلقة بين الأطراف.
    """
    adj = {}
    for req in requests:
        adj.setdefault(req.offering, []).append(req)

    found_cycles = []

    def dfs(start_item: str, current_item: str, path: List[SwapRequest], visited_users: set):
        if len(path) >= max_depth:
            return

        if current_item in adj:
            for next_req in adj[current_item]:
                if next_req.user_id in visited_users:
                    continue
                
                # إذا وصلنا إلى الشرف الأولي، تم إغلاق السلسلة/الدائرة بنجاح!
                if next_req.desiring == start_item:
                    found_cycles.append(path + [next_req])
                    return
                
                dfs(
                    start_item=start_item,
                    current_item=next_req.desiring,
                    path=path + [next_req],
                    visited_users=visited_users | {next_req.user_id}
                )

    for req in requests:
        dfs(start_item=req.offering, current_item=req.desiring, path=[req], visited_users={req.user_id})

    return found_cycles

@app.get("/")
def root():
    return {"status": "online", "message": "TradeCycle Engine is Running Successfully"}

@app.get("/requests")
def get_all_requests():
    return {"total": len(db_requests), "requests": db_requests}

@app.post("/requests")
def add_request(req: SwapRequest):
    db_requests.append(req)
    return {"message": "تمت إضافة طلب التبادل بنجاح", "data": req}

@app.get("/match", response_model=List[CycleResponse])
def match_cycles():
    """
    مسار استدعاء الخوارزمية لإيجاد السلاسل المطابقة
    """
    cycles = find_cycles(db_requests)
    
    formatted_results = []
    for cycle in cycles:
        chain = []
        for req in cycle:
            chain.append({
                "user": req.user_id,
                "gives": req.offering,
                "receives": req.desiring
            })
        formatted_results.append({
            "cycle_length": len(chain),
            "chain": chain
        })

    return formatted_results