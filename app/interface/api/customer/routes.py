from fastapi import APIRouter, Depends, Path, HTTPException, status

from app.application.customer.commands.create_customer_service import CreateCustomerCommandService
from app.application.customer.command_inputs import CreateCustomerInput, UpdateCustomerInput
from app.application.customer.query_filter import CustomerFilter
from app.application.customer.queries.get_customer_detail_service import GetCustomerDetailQueryService
from app.application.customer.queries.list_customers_service import ListCustomersQueryService
from app.application.customer.commands.update_customer_service import UpdateCustomerCommandService
from app.application.customer.errors import DuplicateCustomerEmailError, InvalidCustomerInputError
from app.application.common.errors import AuthorizationError, NotFoundError

from app.domain.user.models import User

from app.interface.api.customer.deps import (
    get_customer_detail_query_service,
    get_customer_list_filter,
    get_customer_list_query_service,
    get_create_customer_service,
    get_update_customer_service,
)
from app.interface.api.auth.deps import get_current_user
from app.interface.api.customer.schemas import (
    CustomerListResponse,
    CustomerSummaryResponse,
    CustomerDetailResponse,
    CreateCustomerRequest,
    CustomerBasicResponse,
    UpdateCustomerRequest,
)


router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=CustomerListResponse)
def list_customers(
    filters: CustomerFilter = Depends(get_customer_list_filter),
    current_user: User = Depends(get_current_user),
    service: ListCustomersQueryService = Depends(get_customer_list_query_service),
) -> CustomerListResponse:
    """顧客一覧を取得するエンドポイント。"""

    result = service.list_customers(current_user=current_user, filters=filters)

    return CustomerListResponse(
        total_count=result.total_count,
        page=result.page,
        page_size=result.page_size,
        customer_summaries=[CustomerSummaryResponse(**summary.__dict__) for summary in result.customer_summaries],
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
)
def get_customer_detail(
    customer_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    service: GetCustomerDetailQueryService = Depends(get_customer_detail_query_service),
) -> CustomerDetailResponse:
    """顧客詳細を取得するエンドポイント。

    - 認証必須（current_user 前提）
    - 指定された customer_id の顧客詳細を返す
    """

    try:
        # Application 層のユースケースを実行
        detail_rm = service.get_customer_detail(
            current_user=current_user,
            customer_id=customer_id,
        )
    except AuthorizationError as exc:
        # 認可エラー → 403 Forbidden（または 401 にしたければここで調整）
        raise HTTPException(
            status_code=401,
            detail="You are not allowed to view this customer.",
        ) from exc
    except NotFoundError as exc:
        # 顧客が存在しない → 404 Not Found
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        ) from exc

    # ReadModel → API レスポンスへの変換
    return CustomerDetailResponse.from_read_model(detail_rm)


# --- 顧客作成 ---
@router.post(
    "/",
    summary="顧客の新規作成",
    description="指定した店舗に新しい顧客を作成します。",
    response_model=CustomerBasicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    body: CreateCustomerRequest,
    current_user: User = Depends(get_current_user),
    service: CreateCustomerCommandService = Depends(get_create_customer_service),
) -> CustomerBasicResponse:
    """顧客を新規作成するエンドポイント."""

    # 1. API のリクエストボディ → application 用の Input DTO に変換
    create_input = CreateCustomerInput(
        shop_id=body.shop_id,
        email=body.email,
        name=body.name,
        status=body.status,
        assigned_to_user_id=body.assigned_to_user_id,
    )

    # 2. アプリケーションサービスを呼び出して顧客作成
    result = service.create_customer(
        current_user=current_user,
        data=create_input,
    )

    # 3. ReadModel → API レスポンススキーマへ変換
    return CustomerBasicResponse.from_read_model(result)


@router.patch(
    "/{customer_id}",
    summary="顧客情報の更新",
    description="指定した顧客の基本情報（名前・メールアドレス・担当者・ステータス）を部分的に更新します。",
    response_model=CustomerBasicResponse,
    status_code=status.HTTP_200_OK,
)
def update_customer(
    customer_id: int,
    body: UpdateCustomerRequest,
    current_user: User = Depends(get_current_user),
    service: UpdateCustomerCommandService = Depends(get_update_customer_service),
) -> CustomerBasicResponse:
    """顧客を部分更新するエンドポイント."""

    # 1. API のリクエストボディ → application 用の Input DTO に変換
    input_data = UpdateCustomerInput(
        name=body.name,
        email=body.email,
        status=body.status,
        assigned_to_user_id=body.assigned_to_user_id,
    )

    # 2. アプリケーションサービスを呼び出して更新
    try:
        result = service.update_customer(
            current_user=current_user,
            customer_id=customer_id,
            data=input_data,
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作を行う権限がありません。",
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された顧客が見つかりません。",
        )
    except DuplicateCustomerEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except InvalidCustomerInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 3. ReadModel → API レスポンススキーマへ変換
    return CustomerBasicResponse.from_read_model(result)
