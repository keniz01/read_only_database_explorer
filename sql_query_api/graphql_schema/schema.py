import strawberry
from strawberry.extensions import QueryDepthLimiter
from routes.sql_query_controller import Query

schema = strawberry.Schema(query=Query, extensions=[QueryDepthLimiter(max_depth=6)])
