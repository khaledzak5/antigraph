from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import base64
from io import BytesIO
import qrcode

from ..database import get_db
from ..deps_auth import require_doc, get_current_user
from ..models import FirstAidBox, FirstAidBoxItem
from ..utils_college import get_user_college, filter_by_college, prevent_cross_college_access

router = APIRouter(prefix="/first-aid", tags=["FirstAid"])
templates = Jinja2Templates(directory="app/templates")

# ===================== صفحة عامة للصندوق (بدون تسجيل دخول) =====================
@router.get("/boxes/{box_id}/public", include_in_schema=False)
def box_public_detail(request: Request, box_id: int, db: Session = Depends(get_db)):
    """صفحة عامة تعرض محتويات الصندوق وسجلات الإضافة وتواريخ الصلاحية بدون تسجيل دخول"""
    from datetime import date
    
    box = db.query(FirstAidBox).filter(FirstAidBox.id == box_id).first()
    if not box:
        raise HTTPException(status_code=404, detail="الصندوق غير موجود")
    
    # توليد QR code يشير للصفحة العامة
    qr_url = f"{request.base_url}first-aid/boxes/{box_id}/public"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # تحويل الصورة إلى base64 لعرضها في HTML
    img_io = BytesIO()
    qr_img.save(img_io, format='PNG')
    img_io.seek(0)
    qr_base64 = base64.b64encode(img_io.getvalue()).decode()
    qr_data_url = f"data:image/png;base64,{qr_base64}"
    
    return templates.TemplateResponse("first_aid/box_public.html", {
        "request": request,
        "box": box,
        "items": box.items,
        "today": date.today(),
        "public": True,
        "qr_code": qr_data_url
    })

# ===================== الداشبورد الرئيسي =====================
@router.get("/", include_in_schema=False)
def fa_index(
    request: Request,
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """الصفحة الرئيسية للإسعافات"""
    # الحصول على كلية المستخدم
    user_college = get_user_college(current_user)
    
    # فلترة الصناديق حسب الكلية
    query = db.query(FirstAidBox)
    query = filter_by_college(query, FirstAidBox, current_user)
    boxes = query.all()
    
    return templates.TemplateResponse("first_aid/index.html", {
        "request": request,
        "boxes": boxes,
        "box_count": len(boxes)
    })

# ===================== قائمة الصناديق =====================
@router.get("/boxes")
def boxes_list(
    request: Request,
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """قائمة جميع صناديق الإسعافات الخاصة بالكلية"""
    # الحصول على كلية المستخدم
    user_college = get_user_college(current_user)
    
    # فلترة الصناديق حسب الكلية
    query = db.query(FirstAidBox)
    query = filter_by_college(query, FirstAidBox, current_user)
    boxes = query.all()
    
    return templates.TemplateResponse("first_aid/boxes_list.html", {
        "request": request,
        "boxes": boxes
    })

# ===================== إنشاء صندوق جديد =====================
@router.get("/boxes/create")
def boxes_create_form(request: Request, user=Depends(require_doc)):
    """نموذج إنشاء صندوق جديد"""
    return templates.TemplateResponse("first_aid/box_form.html", {
        "request": request,
        "mode": "create"
    })

@router.post("/boxes/create")
def boxes_create(
    request: Request,
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    box_name: str = Form(...),
    location: str = Form(...)
):
    """إنشاء صندوق إسعافات جديد"""
    try:
        # الحصول على كلية المستخدم
        user_college = get_user_college(current_user)
        
        if not user_college:
            raise HTTPException(status_code=403, detail="لا يمكن إنشاء صندوق بدون تخصيص كلية")
        
        new_box = FirstAidBox(
            box_name=box_name,
            location=location,
            college_id=user_college,  # حفظ كلية الطبيب
            created_by_user_id=user.id
        )
        db.add(new_box)
        db.commit()
        db.refresh(new_box)
        return RedirectResponse(url=f"/first-aid/boxes/{new_box.id}", status_code=303)
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))

# ===================== عرض تفاصيل الصندوق =====================
@router.get("/boxes/{box_id}")
def box_detail(
    request: Request,
    box_id: int,
    msg: str = Query(default=None),
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """عرض تفاصيل صندوق معين"""
    from datetime import date
    
    box = db.query(FirstAidBox).filter(FirstAidBox.id == box_id).first()
    if not box:
        raise HTTPException(status_code=404, detail="الصندوق غير موجود")
    
    # التحقق من الوصول بناءً على الكلية
    if box.college_id:
        prevent_cross_college_access(current_user, box.college_id)
    
    # تحديث آخر تاريخ مراجعة عند الدخول على الصندوق
    box.last_reviewed_at = datetime.now()
    db.commit()
    
    # توليد QR code يشير للصفحة العامة
    qr_url = f"{request.base_url}first-aid/boxes/{box_id}/public"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # تحويل الصورة إلى base64 لعرضها في HTML
    img_io = BytesIO()
    qr_img.save(img_io, format='PNG')
    img_io.seek(0)
    qr_base64 = base64.b64encode(img_io.getvalue()).decode()
    qr_data_url = f"data:image/png;base64,{qr_base64}"
    
    return templates.TemplateResponse("first_aid/box_detail.html", {
        "request": request,
        "box": box,
        "items": box.items,
        "today": date.today(),
        "msg": msg,
        "qr_code": qr_data_url
    })

# ===================== إضافة دواء للصندوق =====================
@router.get("/boxes/{box_id}/add-item")
def add_item_form(
    request: Request,
    box_id: int,
    error: str = Query(default=None),
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """نموذج إضافة دواء للصندوق"""
    box = db.query(FirstAidBox).filter(FirstAidBox.id == box_id).first()
    if not box:
        raise HTTPException(status_code=404, detail="الصندوق غير موجود")
    
    # التحقق من الوصول بناءً على الكلية
    if box.college_id:
        prevent_cross_college_access(current_user, box.college_id)
    
    # جلب قائمة الأدوية من قاعدة البيانات مع الكميات المتوفرة، مفلترة حسب الطبيب الحالي فقط
    drugs = []
    if current_user and current_user.doctor_college:
        rows = db.execute(text('''
            SELECT d.id, d.trade_name, d.generic_name, d.strength, d.form, d.unit,
                   COALESCE(ps.balance_qty,0) AS available_quantity
            FROM drugs d
            LEFT JOIN pharmacy_stock ps ON ps.drug_id = d.id
            WHERE d.is_active=TRUE AND d.college_id=:college_id AND d.created_by=:user_id
            ORDER BY d.trade_name
        '''), {"college_id": current_user.doctor_college, "user_id": current_user.id}).mappings().all()
        for row in rows:
            drugs.append({
                "id": row["id"],
                "trade_name": row["trade_name"],
                "generic_name": row["generic_name"],
                "strength": row["strength"],
                "form": row["form"],
                "unit": row["unit"],
                "available_quantity": row["available_quantity"] or 0
            })
    return templates.TemplateResponse("first_aid/add_item.html", {
        "request": request,
        "box": box,
        "drugs": drugs,
        "error": error
    })

@router.post("/boxes/{box_id}/add-item")
def add_item(
    request: Request,
    box_id: int,
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    drug_name: str = Form(...),
    drug_code: str = Form(default=None),
    quantity: int = Form(...),
    unit: str = Form(default="عدد"),
    expiry_date: str = Form(default=None),
    notes: str = Form(default=None)
):
    """إضافة دواء للصندوق"""
    try:
        # الحصول على كلية المستخدم
        user_college = get_user_college(current_user)
        
        if not user_college:
            raise HTTPException(status_code=403, detail="لا يمكن إضافة دواء بدون تخصيص كلية")
        
        box = db.query(FirstAidBox).filter(FirstAidBox.id == box_id).first()
        if not box:
            raise HTTPException(status_code=404, detail="الصندوق غير موجود")
        
        # التحقق من الوصول بناءً على الكلية
        if box.college_id:
            prevent_cross_college_access(current_user, box.college_id)
        
        # التحقق من أن الكمية لا تتجاوز الحد المتاح في الصيدلية
        if drug_code:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from excel_data_reference import get_drug_by_code, get_drug_stock
                
                # محاولة الحصول على بيانات الدواء من الصيدلية
                drug_stock = get_drug_stock(drug_code)
                
                if drug_stock:
                    available_quantity = drug_stock.get('stock_qty', 0)
                    if quantity > available_quantity:
                        error_msg = f"الكمية المطلوبة ({quantity}) تتجاوز المتاح في المخزون ({available_quantity}). الرجاء اختيار كمية أقل."
                        return RedirectResponse(
                            url=f"/first-aid/boxes/{box_id}/add-item?error={error_msg}",
                            status_code=303
                        )
            except Exception:
                # إذا فشل التحقق، نسمح بالإضافة (قد لا توجد بيانات عن الدواء)
                pass
        
        expiry_date_obj = None
        if expiry_date:
            try:
                expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            except Exception:
                pass
        
        new_item = FirstAidBoxItem(
            box_id=box_id,
            college_id=user_college,  # تعيين الكلية تلقائياً
            drug_name=drug_name,
            drug_code=drug_code,
            quantity=quantity,
            unit=unit,
            expiry_date=expiry_date_obj,
            notes=notes
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # ===== تسجيل حركة المخزون وخصم الكمية من الرصيد =====
        if drug_code:
            try:
                from sqlalchemy.orm import Session
                
                # 1. ابحث عن الدواء بالكود
                drug_row = db.execute(text(
                    'SELECT id FROM drugs WHERE drug_code = :code'
                ), {'code': drug_code}).fetchone()
                
                if drug_row:
                    drug_id = drug_row[0]
                    
                    # 2. تحديث أو إدراج في المخزن (warehouse) مع حفظ الكلية
                    existing_warehouse = db.execute(text(
                        'SELECT id FROM warehouse_stock WHERE drug_id = :did'
                    ), {'did': drug_id}).fetchone()
                    
                    if existing_warehouse:
                        db.execute(text('''
                            UPDATE warehouse_stock
                            SET balance_qty = balance_qty - :qty,
                                college = :college,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE drug_id = :did
                        '''), {'qty': quantity, 'did': drug_id, 'college': user_college})
                    else:
                        db.execute(text('''
                            INSERT INTO warehouse_stock (drug_id, balance_qty, college)
                            VALUES (:did, :qty, :college)
                        '''), {'did': drug_id, 'qty': -quantity, 'college': user_college})
                    
                    # 3. تحديث أو إدراج في الصيدلية (pharmacy) مع حفظ الكلية
                    existing_pharmacy = db.execute(text(
                        'SELECT id FROM pharmacy_stock WHERE drug_id = :did'
                    ), {'did': drug_id}).fetchone()
                    
                    if existing_pharmacy:
                        db.execute(text('''
                            UPDATE pharmacy_stock
                            SET balance_qty = balance_qty - :qty,
                                college = :college,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE drug_id = :did
                        '''), {'qty': quantity, 'did': drug_id, 'college': user_college})
                    else:
                        db.execute(text('''
                            INSERT INTO pharmacy_stock (drug_id, balance_qty, college)
                            VALUES (:did, :qty, :college)
                        '''), {'did': drug_id, 'qty': -quantity, 'college': user_college})
                    
                    # 4. سجل الحركة في جدول حركات الأدوية
                    db.execute(text('''
                        INSERT INTO drug_transactions 
                        (drug_id, drug_code, transaction_type, quantity_change, 
                         source, destination, notes, created_by)
                        VALUES (:did, :code, :type, :qty, :src, :dst, :notes, :uid)
                    '''), {
                        'did': drug_id,
                        'code': drug_code,
                        'type': 'warehouse_to_box',
                        'qty': -quantity,
                        'src': 'warehouse',
                        'dst': f'box_{box_id}',
                        'notes': f'إضافة للصندوق: {box.box_name}',
                        'uid': user.id
                    })
                    
                    db.commit()
                    print(f"✓ تم خصم {quantity} من الرصيد")
            except Exception as e:
                print(f"Warning: Failed to update stock: {e}")
                # لا نتوقف عن العملية حتى لو فشل الخصم
        
        return RedirectResponse(url=f"/first-aid/boxes/{box_id}?msg=item_added_stock_deducted", status_code=303)
    except Exception as ex:
        db.rollback()
        error_msg = str(ex)
        return RedirectResponse(
            url=f"/first-aid/boxes/{box_id}/add-item?error={error_msg}",
            status_code=303
        )

# ===================== حذف عنصر من الصندوق =====================
@router.post("/boxes/{box_id}/items/{item_id}/delete")
def delete_item(
    box_id: int,
    item_id: int,
    user=Depends(require_doc),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """حذف دواء من الصندوق وإرجاع الكمية للمخزن"""
    try:
        # التحقق من الوصول للصندوق أولاً
        box = db.query(FirstAidBox).filter(FirstAidBox.id == box_id).first()
        if not box:
            raise HTTPException(status_code=404, detail="الصندوق غير موجود")
        
        if box.college_id:
            prevent_cross_college_access(current_user, box.college_id)
        
        item = db.query(FirstAidBoxItem).filter(
            FirstAidBoxItem.id == item_id,
            FirstAidBoxItem.box_id == box_id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="العنصر غير موجود")
        
        # حفظ البيانات قبل الحذف
        drug_code = item.drug_code
        quantity = item.quantity
        drug_name = item.drug_name
        
        # حذف العنصر
        db.delete(item)
        db.commit()
        
        # ===== إرجاع الكمية للمخزن عند الحذف =====
        if drug_code:
            try:
                # 1. ابحث عن الدواء بالكود
                drug_row = db.execute(text(
                    'SELECT id FROM drugs WHERE drug_code = :code'
                ), {'code': drug_code}).fetchone()
                
                if drug_row:
                    drug_id = drug_row[0]
                    
                    # 2. أرجع الكمية لرصيد المخزن (warehouse)
                    db.execute(text('''
                        UPDATE warehouse_stock
                        SET balance_qty = balance_qty + :qty,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE drug_id = :did
                    '''), {'qty': quantity, 'did': drug_id})
                    
                    # 3. أرجع الكمية لرصيد الصيدلية (pharmacy)
                    db.execute(text('''
                        UPDATE pharmacy_stock
                        SET balance_qty = balance_qty + :qty,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE drug_id = :did
                    '''), {'qty': quantity, 'did': drug_id})
                    
                    # 4. سجل الحركة
                    db.execute(text('''
                        INSERT INTO drug_transactions 
                        (drug_id, drug_code, transaction_type, quantity_change, 
                         source, destination, notes, created_by)
                        VALUES (:did, :code, :type, :qty, :src, :dst, :notes, :uid)
                    '''), {
                        'did': drug_id,
                        'code': drug_code,
                        'type': 'box_return',
                        'qty': quantity,
                        'src': f'box_{box_id}',
                        'dst': 'warehouse',
                        'notes': f'إرجاع من صندوق - حذف عنصر',
                        'uid': user.id
                    })
                    
                    db.commit()
            except Exception as e:
                print(f"Warning: Failed to restore stock on delete: {e}")
        
        return RedirectResponse(url=f"/first-aid/boxes/{box_id}?msg=item_deleted_stock_restored", status_code=303)
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))
