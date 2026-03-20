create database QUANLYCUAHANG;


---TẠO BẢNG EMPLOYEES
create table Employees
(
	EmployeeID int not null,
	EmployeeName nvarchar(50) not null,
	EmployeeGender nvarchar(50),
	EmployeePhone varchar(15) not null,
	EmployeeEmail nvarchar(50),
	HireDate date not null,
	Status nvarchar(50) not null,
	EmployeeType nvarchar(50) not null,
	ManagerID int
)

---TẠO BẢNG ACCOUNTS
create table Accounts
(
	AccountID int not null,
	EmployeeID int not null,
	Username varchar(50) not null,
	Password varchar(255) not null,
	Role nvarchar(50) not null,
	Status nvarchar(50) not null
)

---TẠO BẢNG CUSTOMERS
create table Customers
(
	CustomerID int not null,
	CustomerName nvarchar(50) not null,
	CustomerGender nvarchar(10),
	CustomerPhone varchar(15) not null,
	LoyaltyPoints int not null
)

---TẠO BẢNG EMPLOYEE_SKILL
create table Skills
(
	EmployeeID int not null,
	Skill nvarchar(50) not null
)

---TẠO BẢNG PART_TIME
create table Part_Time
(
	EmployeeID int not null,
	HourlyRate decimal (18,2) not null,
	WorkingHoursPerWeek int not null
)

---TẠO BẢNG FULL_TIME
create table Full_time
(
	EmployeeID int not null,
	MonthlySalary decimal (18,2) not null,
	Position nvarchar(50) not null
)

---TẠO BẢNG SUPPLIERS
create table Suppliers
(
	SupplierID int not null,
	SupplierName nvarchar(50) not null,
	SupplierPhone varchar(15) not null,
	SupplierEmail nvarchar(50),
	SupplierAddress nvarchar(50)
)

---TẠO BẢNG CATEGORIES
create table Categories
(
	CategoryID int not null,
	CategoryName nvarchar(50) not null,
	Description nvarchar(max)
)

---TẠO BẢNG PRODUCTS
create table Products
(
	ProductID int not null,
	CategoryID int not null,
	ProductName nvarchar(50) not null,
	UnitPrice decimal (18,2) not null,
	UnitsInStock int not null,
	Status nvarchar(50) not null
)

---TẠO BẢNG ORDERS
create table Orders
(
	OrderID int not null,
	CustomerID int not null,
	EmployeeID int not null,
	OrderDate date not null,
	TotalAmount decimal (18,2) not null,
	Status nvarchar(50) not null
)

---TẠO BẢNG ORDER_DETAILS
create table Order_Details
(
	OrderID int not null,
	ProductID int not null,
	OrderedQuantity int not null,
	Discount decimal (18,2),
	SubTotal decimal (18,2) not null
)

---TẠO BẢNG PURCHASE_ORDERS
create table Purchase_Orders
(
	PurchaseOrderID int not null,
	SupplierID int not null,
	EmployeeID int not null,
	PurchasedDate date not null,
	ExpectedDate date not null,
	ReceivedDate date,
	TotalAmount decimal (18,2) not null,
	Status nvarchar(50) not null
)

---TẠO BẢNG PURCHASE_DETAILS
create table Purchase_Details
(
	PurchaseOrderID int not null,
	ProductID int not null,
	PurchasedQuantity int not null,
	UnitCost decimal (18,2) not null,
	SubTotal decimal (18,2) not null
)

---TẠO BẢNG PROMOTIONS
create table Promotions
(
	PromotionID int not null,
	PromotionName nvarchar(50) not null,
	PromotionForm nvarchar(50) not null,
	StartDate date not null,
	EndDate date not null,
	Status nvarchar(50) not null
)

---TẠO BẢNG PROMOTION_DETAILS
create table Promotion_Details
(
	PromotionID int not null,
	ProductID int not null,
	ApplicableDate date not null,
	DiscountRate decimal (18,2),
	DiscountValue decimal (18,2),
	DiscountedPrice decimal (18,2) not null
)

---TẠO BẢNG BILLS
create table Bills
(
	BillID int not null,
	OrderID int not null,
	PaymentDate date not null,
	PaymentAmount decimal (18,2) not null,
	PaymentMethod nvarchar(50)
)

---PRIMARY KEY
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG CUSTOMERS
ALTER TABLE Customers ADD CONSTRAINT pk_Customers PRIMARY KEY	(CustomerID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG ACCOUNTS
ALTER TABLE Accounts ADD CONSTRAINT pk_Accounts PRIMARY KEY (AccountID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG EMPLOYEES
ALTER TABLE Employees ADD CONSTRAINT pk_Employees PRIMARY KEY (EmployeeID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG SKILLS
ALTER TABLE Skills ADD CONSTRAINT pk_Skills PRIMARY KEY (EmployeeID, Skill)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PART_TIME
ALTER TABLE Part_Time ADD CONSTRAINT pk_Part_Time PRIMARY KEY (EmployeeID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG FULL_TIME
ALTER TABLE Full_Time ADD CONSTRAINT pk_Full_Time PRIMARY KEY (EmployeeID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG SUPPLIERS
ALTER TABLE Suppliers ADD CONSTRAINT pk_Suppliers PRIMARY KEY (SupplierID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PRODUCTS
ALTER TABLE Products ADD CONSTRAINT pk_Products PRIMARY KEY (ProductID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG CATEGORIES
ALTER TABLE Categories ADD CONSTRAINT pk_Categories PRIMARY KEY (CategoryID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG ORDERS
ALTER TABLE Orders ADD CONSTRAINT pk_Orders PRIMARY KEY (OrderID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG ORDER_DETAILS
ALTER TABLE Order_Details ADD CONSTRAINT pk_Order_Details PRIMARY KEY (OrderID, ProductID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG BILLS
ALTER TABLE Bills ADD CONSTRAINT pk_Bills PRIMARY KEY (BillID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PURCHASE_ORDERS
ALTER TABLE Purchase_Orders ADD CONSTRAINT pk_Purchase_Orders PRIMARY KEY (PurchaseOrderID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PURCHASE_DETAILS
ALTER TABLE Purchase_Details ADD CONSTRAINT pk_Purchase_Details PRIMARY KEY (PurchaseOrderID, ProductID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PROMOTIONS
ALTER TABLE Promotions ADD CONSTRAINT pk_Promotions PRIMARY KEY (PromotionID)
---RÀNG BUỘC KHÓA CHÍNH CHO BẢNG PROMOTION_DETAILS
ALTER TABLE Promotion_Details ADD CONSTRAINT pk_Promotion_Details PRIMARY KEY (PromotionID, ProductID)


---FOREIGN KEY
---RÀNG BUỘC KHÓA NGOẠI BẢNG EMPLOYEES (Quan hệ đệ quy quản lý)
ALTER TABLE Employees ADD CONSTRAINT fk_Employees_Manager 
FOREIGN KEY (ManagerID) REFERENCES Employees(EmployeeID);
---RÀNG BUỘC KHÓA NGOẠI BẢNG ACCOUNTS
ALTER TABLE Accounts ADD CONSTRAINT fk_Accounts_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
---RÀNG BUỘC KHÓA NGOẠI BẢNG SKILLS
ALTER TABLE Skills ADD CONSTRAINT fk_Skills_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE
---RÀNG BUỘC KHÓA NGOẠI BẢNG PART_TIME
ALTER TABLE Part_time ADD CONSTRAINT fk_PartTime_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE
---RÀNG BUỘC KHÓA NGOẠI BẢNG FULL_TIME
ALTER TABLE Full_time ADD CONSTRAINT fk_FullTime_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE
---RÀNG BUỘC KHÓA NGOẠI BẢNG PRODUCTS
ALTER TABLE Products ADD CONSTRAINT fK_Products_Categories 
FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
---RÀNG BUỘC KHÓA NGOẠI BẢNG ORDERS
ALTER TABLE Orders ADD CONSTRAINT fK_Orders_Customers 
FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID);
ALTER TABLE Orders ADD CONSTRAINT fK_Orders_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
---RÀNG BUỘC KHÓA NGOẠI BẢNG ORDER_DETAILS
ALTER TABLE Order_details ADD CONSTRAINT fK_OD_Orders 
FOREIGN KEY (OrderID) REFERENCES Orders(OrderID);
ALTER TABLE Order_details ADD CONSTRAINT fK_OD_Products 
FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
---RÀNG BUỘC KHÓA NGOẠI BẢNG BILLS
ALTER TABLE Bills ADD CONSTRAINT fK_Bills_Orders 
FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
---RÀNG BUỘC KHÓA NGOẠI BẢNG PURCHASE_ORDERS
ALTER TABLE Purchase_orders ADD CONSTRAINT fK_PO_Suppliers 
FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID);
ALTER TABLE Purchase_orders ADD CONSTRAINT fK_PO_Employees 
FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
---RÀNG BUỘC KHÓA NGOẠI PURCHASE_DETAILS
ALTER TABLE Purchase_details ADD CONSTRAINT fK_PD_Purchase_orders 
FOREIGN KEY (PurchaseOrderID) REFERENCES Purchase_orders(PurchaseOrderID);
ALTER TABLE Purchase_details ADD CONSTRAINT fK_PD_Products 
FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
---RÀNG BUỘC KHÓA NGOẠI PROMOTION_DETAILS
ALTER TABLE Promotion_details ADD CONSTRAINT fK_PromD_Promotions 
FOREIGN KEY (PromotionID) REFERENCES Promotions(PromotionID);
ALTER TABLE Promotion_details ADD CONSTRAINT fK_PromD_Products 
FOREIGN KEY (ProductID) REFERENCES Products(ProductID)

---UNIQUE
---ĐẢM BẢO SĐT KHÁCH HÀNG KHÔNG BỊ TRÙNG
ALTER TABLE Customers ADD CONSTRAINT UQ_Customers_Phone UNIQUE (CustomerPhone)
---ĐẢM BẢO 1 NHÂN VIÊN CHỈ CÓ TỐI ĐA 1 TÀI KHOẢN
ALTER TABLE Accounts ADD CONSTRAINT UQ_Accounts_EmployeeID UNIQUE (EmployeeID);
---ĐẢM BẢO USERNAME KHÔNG BỊ TRÙNG
ALTER TABLE Accounts ADD CONSTRAINT UQ_Accounts_Username UNIQUE (Username)
---ĐẢM BẢO SĐT VÀ EMAIL NHÂN VIÊN KHÔNG BỊ TRÙNG
ALTER TABLE Employees ADD CONSTRAINT UQ_Employees_Phone UNIQUE (EmployeePhone);
ALTER TABLE Employees ADD CONSTRAINT UQ_Employees_Email UNIQUE (EmployeeEmail)
---ĐẢM BẢO SĐT VÀ EMAIL NHÀ CUNG CẤP KHÔNG BỊ TRÙNG
ALTER TABLE Suppliers ADD CONSTRAINT UQ_Suppliers_Phone UNIQUE (SupplierPhone);
ALTER TABLE Suppliers ADD CONSTRAINT UQ_Suppliers_Email UNIQUE (SupplierEmail)
---ĐẢM BẢO TÊN DANH MỤC LÀ DUY NHẤT
ALTER TABLE Categories ADD CONSTRAINT UQ_Categories_Name UNIQUE (CategoryName)
---ĐẢM BẢO 1 ĐƠN HÀNG CHỈ CÓ TỐI ĐA 1 HÓA ĐƠN THANH TOÁN (BILL)
ALTER TABLE Bills ADD CONSTRAINT UQ_Bills_OrderID UNIQUE (OrderID);
---ĐẢM BẢO TÊN CHƯƠNG TRÌNH KHUYẾN MÃI LÀ DUY NHẤT
ALTER TABLE Promotions ADD CONSTRAINT UQ_Promotion_Name UNIQUE (PromotionName)

---CHECK
---RÀNG BUỘC CHO BẢNG EMPLOYEES
---ĐẢM BẢO GIỚI TÍNH NHÂN VIÊN HỢP LỆ
ALTER TABLE Employees ADD CONSTRAINT CHK_Employees_Gender 
CHECK (EmployeeGender IN (N'Nam', N'Nữ', N'Khác'))
---ĐẢM BẢO TRẠNG THÁI NHÂN VIÊN HỢP LỆ
ALTER TABLE Employees ADD CONSTRAINT CHK_Employees_Status 
CHECK (Status IN (N'Đang làm việc', N'Đã nghỉ việc'))
---ĐẢM BẢO LOẠI NHÂN VIÊN HỢP LỆ
ALTER TABLE Employees ADD CONSTRAINT CHK_Employees_Type 
CHECK (EmployeeType IN (N'Part_time', N'Full_time'))

---RÀNG BUỘC CHO BẢNG ACCOUNTS
---ĐẢM BẢO VAI TRÒ TÀI KHOẢN HỢP LỆ
ALTER TABLE Accounts ADD CONSTRAINT CHK_Accounts_Role 
CHECK (Role IN (N'Quản lý cửa hàng', N'Nhân viên bán hàng', N'Nhân viên kho'))
---ĐẢM BẢO TRẠNG THÁI TÀI KHOẢN HỢP LỆ
ALTER TABLE Accounts ADD CONSTRAINT CHK_Accounts_Status 
CHECK (Status IN (N'Đang hoạt động', N'Đã bị khóa'))

---RÀNG BUỘC CHO BẢNG CUSTOMERS
---ĐẢM BẢO GIỚI TÍNH KHÁCH HÀNG HỢP LỆ
ALTER TABLE Customers ADD CONSTRAINT CHK_Customers_Gender 
CHECK (CustomerGender IN (N'Nam', N'Nữ', N'Khác'))
---ĐẢM BẢO ĐIỂM TÍCH LŨY KHÔNG ÂM
ALTER TABLE Customers ADD CONSTRAINT CHK_LoyaltyPoints 
CHECK (LoyaltyPoints >= 0)

---RÀNG BUỘC CHO BẢNG PART_TIME
---ĐẢM BẢO LƯƠNG GIỜ PHẢI LỚN HƠN 0
ALTER TABLE Part_Time ADD CONSTRAINT CHK_HourlyRate 
CHECK (HourlyRate > 0)
---ĐẢM BẢO SỐ GIỜ LÀM VIỆC/TUẦN HỢP LÝ (1-168 giờ)
ALTER TABLE Part_Time ADD CONSTRAINT CHK_WorkingHours 
CHECK (WorkingHoursPerWeek BETWEEN 1 AND 168)

---RÀNG BUỘC CHO BẢNG FULL_TIME
---ĐẢM BẢO LƯƠNG THÁNG PHẢI LỚN HƠN 0
ALTER TABLE Full_Time ADD CONSTRAINT CHK_MonthlySalary 
CHECK (MonthlySalary > 0)

---RÀNG BUỘC CHO BẢNG PRODUCTS
---ĐẢM BẢO ĐƠN GIÁ SẢN PHẨM PHẢI LỚN HƠN 0
ALTER TABLE Products ADD CONSTRAINT CHK_UnitPrice 
CHECK (UnitPrice > 0)
---ĐẢM BẢO SỐ LƯỢNG TỒN KHO KHÔNG ÂM
ALTER TABLE Products ADD CONSTRAINT CHK_UnitsInStock 
CHECK (UnitsInStock >= 0)
---ĐẢM BẢO TRẠNG THÁI SẢN PHẨM LÀ "CÒN HÀNG" HOẶC "HẾT HÀNG"
ALTER TABLE Products ADD CONSTRAINT CHK_Products_Status 
CHECK (Status IN (N'Còn hàng', N'Hết hàng'))

---RÀNG BUỘC CHO BẢNG ORDERS
---ĐẢM BẢO TRẠNG THÁI ĐƠN HÀNG LÀ "ĐÃ THANH TOÁN" HOẶC "CHƯA THANH TOÁN"
ALTER TABLE Orders ADD CONSTRAINT CHK_Orders_Status 
CHECK (Status IN (N'Đã thanh toán', N'Chưa thanh toán'))
---ĐẢM BẢO TỔNG TIỀN ĐƠN HÀNG KHÔNG ÂM
ALTER TABLE Orders ADD CONSTRAINT CHK_TotalAmount 
CHECK (TotalAmount >= 0)

---RÀNG BUỘC CHO BẢNG ORDER_DETAILS
---ĐẢM BẢO SỐ LƯỢNG BÁN HÀNG PHẢI LỚN HƠN 0
ALTER TABLE Order_Details ADD CONSTRAINT CHK_OrderedQuantity 
CHECK (OrderedQuantity > 0)
---ĐẢM BẢO CHIẾT KHẤU KHÔNG ÂM (0% là không chiết khấu)
ALTER TABLE Order_Details ADD CONSTRAINT CHK_Order_Discount 
CHECK (Discount >= 0)
---ĐẢM BẢO THÀNH TIỀN KHÔNG ÂM
ALTER TABLE Order_Details ADD CONSTRAINT CHK_SubTotal 
CHECK (SubTotal >= 0)

---RÀNG BUỘC CHO BẢNG BILLS
--- ĐẢM BẢO SỐ TIỀN THANH TOÁN PHẢI LỚN HƠN 0
ALTER TABLE Bills ADD CONSTRAINT CHK_PaymentAmount 
CHECK (PaymentAmount > 0)
---ĐẢM BẢO PHƯƠNG THỨC THANH TOÁN LÀ "TIỀN MẶT", "CHUYỂN KHOẢN NGÂN HÀNG" HOẶC "VÍ ĐIỆN TỬ"
ALTER TABLE Bills ADD CONSTRAINT CHK_PaymentMethod 
CHECK (PaymentMethod IN (N'Tiền mặt', N'Chuyển khoản ngân hàng', N'Ví điện tử'))

---RÀNG BUỘC CHO BẢNG PURCHASE_ORDERS
---ĐẢM BẢO TRẠNG THÁI ĐƠN NHẬP HÀNG LÀ "ĐÃ NHẬN HÀNG" HOẶC "CHƯA NHẬN HÀNG"
ALTER TABLE Purchase_Orders ADD CONSTRAINT CHK_PurchaseOrders_Status 
CHECK (Status IN (N'Đã nhận hàng', N'Chưa nhận hàng'))
---ĐẢM BẢO TỔNG TIỀN ĐƠN NHẬP KHÔNG ÂM
ALTER TABLE Purchase_Orders ADD CONSTRAINT CHK_Purchase_TotalAmount 
CHECK (TotalAmount >= 0)
---ĐẢM BẢO NGÀY NHẬN HÀNG DỰ KIẾN PHẢI SAU HOẶC BẰNG NGÀY ĐẶT HÀNG
ALTER TABLE Purchase_Orders ADD CONSTRAINT CHK_Purchase_Dates 
CHECK (ExpectedDate >= PurchasedDate)
---ĐẢM BẢO NGÀY THỰC NHẬN PHẢI SAU HOẶC BẰNG NGÀY ĐẶT MUA (Bỏ qua nếu chưa nhận - NULL)
ALTER TABLE Purchase_Orders ADD CONSTRAINT CHK_Purchase_ReceivedDate 
CHECK (ReceivedDate IS NULL OR ReceivedDate >= PurchasedDate);

---RÀNG BUỘC CHO BẢNG PURCHASE_DETAILS
---ĐẢM BẢO SỐ LƯỢNG ĐẶT MUA PHẢI LỚN HƠN 0
ALTER TABLE Purchase_Details ADD CONSTRAINT CHK_Purchase_Quantity 
CHECK (PurchasedQuantity > 0)
---ĐẢM BẢO ĐƠN GIÁ NHẬP PHẢI LỚN HƠN 0
ALTER TABLE Purchase_Details ADD CONSTRAINT CHK_UnitCost 
CHECK (UnitCost > 0)
---ĐẢM BẢO THÀNH TIỀN KHÔNG ÂM
ALTER TABLE Purchase_Details ADD CONSTRAINT CHK_Purchase_SubTotal 
CHECK (SubTotal >= 0)

---RÀNG BUỘC CHO BẢNG PROMOTIONS
---ĐẢM BẢO TRẠNG THÁI KHUYẾN MÃI LÀ "SẮP DIỄN RA", "ĐANG DIỄN RA" HOẶC "ĐÃ KẾT THÚC"
ALTER TABLE Promotions ADD CONSTRAINT CHK_Promotions_Status 
CHECK (Status IN (N'Sắp diễn ra', N'Đang diễn ra', N'Đã kết thúc'))
---ĐẢM BẢO HÌNH THỨC KHUYẾN MÃI LÀ "GIẢM THEO %" HOẶC "GIẢM THEO GIÁ TRỊ"
ALTER TABLE Promotions ADD CONSTRAINT CHK_Promotions_Form 
CHECK (PromotionForm IN (N'Giảm theo %', N'Giá trị'))
---ĐẢM BẢO NGÀY KẾT THÚC PHẢI SAU HOẶC BẰNG NGÀY BẮT ĐẦU
ALTER TABLE Promotions ADD CONSTRAINT CHK_Promotion_Dates 
CHECK (EndDate >= StartDate)

---RÀNG BUỘC CHO BẢNG PROMOTION_DETAILS
---ĐẢM BẢO TỶ LỆ GIẢM GIÁ TỪ 0% ĐẾN 100%
ALTER TABLE Promotion_Details ADD CONSTRAINT CHK_DiscountRate 
CHECK (DiscountRate BETWEEN 0 AND 100)
---ĐẢM BẢO GIÁ TRỊ GIẢM KHÔNG ÂM
ALTER TABLE Promotion_Details ADD CONSTRAINT CHK_DiscountValue 
CHECK (DiscountValue >= 0)
---ĐẢM BẢO GIÁ SAU KHI CHIẾT KHẤU KHÔNG ÂM
ALTER TABLE Promotion_Details ADD CONSTRAINT CHK_DiscountedPrice 
CHECK (DiscountedPrice >= 0)
---ĐẢM BẢO CHỈ NHẬP 1 TRONG 2: HOẶC RATE, HOẶC VALUE
ALTER TABLE Promotion_Details ADD CONSTRAINT CHK_Promotion_Discount_Input 
CHECK (
    (DiscountRate IS NOT NULL AND DiscountValue IS NULL) 
    OR 
    (DiscountRate IS NULL AND DiscountValue IS NOT NULL)
)


INSERT INTO Employees (EmployeeID, EmployeeName, EmployeeGender, EmployeePhone, EmployeeEmail, HireDate, Status, EmployeeType, ManagerID) VALUES
(1, N'Lê Quốc Chính', N'Nam', '0901000111', N'vuong.le@cuahang.com', '2020-01-10', N'Đang làm việc', N'Full_time', NULL),
(2, N'Trần Công Anh', N'Nam', '0902000222', N'anhtran@cuahang.com', '2021-03-15', N'Đang làm việc', N'Full_time', 1),
(3, N'Nguyễn Hải Nam', N'Nam', '0903000333', N'kietnguyen@cuahang.com', '2022-05-20', N'Đang làm việc', N'Full_time', 1),
(4, N'Hoàng Yến Nhi', N'Nữ', '0904000444', N'thuonghoang@cuahang.com', '2023-08-10', N'Đang làm việc', N'Full_time', 1),
(5, N'Phạm Tiến Nhân', N'Nam', '0905000555', N'caopham@cuahang.com', '2022-11-01', N'Đã nghỉ việc', N'Full_time', 1),
(6, N'Đỗ Minh Long', N'Nam', '0906000666', N'namdo@cuahang.com', '2021-09-05', N'Đang làm việc', N'Full_time', 1),
(7, N'Vũ Thu Phương', N'Nữ', '0907000777', N'hoanvu@cuahang.com', '2023-02-14', N'Đang làm việc', N'Full_time', 1),
(8, N'Bùi Thanh Hảo', N'Nữ', '0908000888', N'haobui@cuahang.com', '2024-01-05', N'Đang làm việc', N'Part_time', 1),
(9, N'Lý Văn Nhất', N'Nam', '0909000999', N'nhatly@cuahang.com', '2023-12-20', N'Đã nghỉ việc', N'Part_time', 1),
(10, N'Đinh Bảo Ly', N'Nữ', '0910000101', N'lydinh@cuahang.com', '2024-03-01', N'Đang làm việc', N'Part_time', 1);


INSERT INTO Accounts (AccountID, EmployeeID, Username, Password, Role, Status) VALUES
(1, 1, 'chinh.le', '123456', N'Quản lý cửa hàng', N'Đang hoạt động'),
(2, 2, 'anh.tran', '123456', N'Nhân viên bán hàng', N'Đang hoạt động'),
(3, 3, 'nam.nguyen', '123456', N'Nhân viên bán hàng', N'Đang hoạt động'),
(4, 4, 'nhi.hoang', '123456', N'Nhân viên bán hàng', N'Đang hoạt động'),
(5, 5, 'nhan.pham', '123456', N'Nhân viên bán hàng', N'Đã bị khóa'),
(6, 6, 'long.do', '123456', N'Nhân viên kho', N'Đang hoạt động'),
(7, 7, 'phuong.vu', '123456', N'Nhân viên kho', N'Đang hoạt động'),
(8, 8, 'hao.bui', '123456', N'Nhân viên bán hàng', N'Đang hoạt động'),
(9, 9, 'nhat.ly', '123456', N'Nhân viên bán hàng', N'Đã bị khóa'),
(10, 10, 'ly.dinh', '123456', N'Nhân viên bán hàng', N'Đang hoạt động');


INSERT INTO Full_Time (EmployeeID, Position, MonthlySalary) VALUES
(1, N'Quản lý cửa hàng', 35000000.00),
(2, N'Nhân viên bán hàng', 20000000.00),
(3, N'Nhân viên bán hàng', 18000000.00),
(4, N'Nhân viên bán hàng', 12000000.00),
(5, N'Nhân viên bán hàng', 15000000.00),
(6, N'Nhân viên kho', 13000000.00),
(7, N'Nhân viên kho', 14000000.00);

INSERT INTO Part_Time (EmployeeID, HourlyRate, WorkingHoursPerWeek) VALUES
(8, 25000.00, 24), 
(9, 30000.00, 20), 
(10, 25000.00, 28);


INSERT INTO Skills (EmployeeID, Skill) VALUES
(1, N'Quản trị cửa hàng'),
(1, N'Chăm sóc khách hàng VIP'),
(2, N'Chăm sóc khách hàng VIP'),
(3, N'Điều phối ca trực'),
(4, N'Xử lý khiếu nại qua điện thoại'),
(5, N'Kỹ năng chốt sale nhanh'),
(6, N'Quản lý xuất nhập tồn'),
(6, N'Tư vấn trực tiếp'),
(7, N'Sắp xếp hàng hóa tối ưu'),
(8, N'Tư vấn trực tiếp'),
(9, N'Tư vấn trực tiếp'),
(10, N'Xử lý khiếu nại qua điện thoại');


INSERT INTO Customers (CustomerID, CustomerName, CustomerGender, CustomerPhone, LoyaltyPoints) VALUES
(1, N'Nguyễn Văn Bằng', N'Nam', '0981110001', 50),
(2, N'Tô Xuân Hương', N'Nữ', '0981110002', 150),
(3, N'Khiêm Triệu Toàn', N'Nam', '0981110003', 0),
(4, N'Hồng Cẩm Đào', N'Nữ', '0981110004', 300),
(5, N'Sơn Duy Đoàn', N'Nam', '0981110005', 20),
(6, N'Nguyễn Thị Bích', N'Nữ', '0981110006', 500),
(7, N'Trần Văn Tài', N'Nam', '0981110007', 80),
(8, N'Nguyễn Thị Tuyết', N'Nữ', '0981110008', 120),
(9, N'Lâm Hồng Ân', N'Nam', '0981110009', 10),
(10, N'Nguyễn Thị Hân Tuyền', N'Nữ', '0981110010', 45);


INSERT INTO Suppliers (SupplierID, SupplierName, SupplierPhone, SupplierEmail, SupplierAddress) VALUES
(1, N'Công ty Apple VN', '02811111111', N'apple@vn.com', N'Quận 1, TP.HCM'), 
(2, N'Tập đoàn Sunhouse', '02822222222', N'contact@sunhouse.vn', N'Cầu Giấy, Hà Nội'), 
(3, N'Công ty Unilever VN', '02833333333', N'cskh@unilever.com', N'Quận 7, TP.HCM'), 
(4, N'Tập đoàn Thiên Long', '02844444444', N'info@thienlong.vn', N'Tân Tạo, TP.HCM'), 
(5, N'LOréal Việt Nam', '02855555555', N'loreal@vn.com', N'Quận 1, TP.HCM'), 
(6, N'Masan Consumer', '02866666666', N'cskh@masan.com', N'Quận 1, TP.HCM'), 
(7, N'Công ty CP Việt Tinh Anh', '02877777777', N'mykingdom@vn.com', N'Quận 10, TP.HCM'), 
(8, N'NXB Kim Đồng', '02888888888', N'info@nxbkimdong.com', N'Hai Bà Trưng, Hà Nội'), 
(9, N'Uniqlo Việt Nam', '02899999999', N'contact@uniqlo.vn', N'Quận 1, TP.HCM'), 
(10, N'Công ty Panasonic VN', '02800000000', N'customer@panasonic.com', N'Đống Đa, Hà Nội');


INSERT INTO Categories (CategoryID, CategoryName, Description) VALUES
(1, N'Điện thoại & Phụ kiện', N'Thiết bị di động thông minh'),
(2, N'Đồ gia dụng nhà bếp', N'Nồi, chảo, máy ép, nồi chiên'),
(3, N'Chăm sóc nhà cửa', N'Bột giặt, nước lau sàn, xịt phòng'),
(4, N'Văn phòng phẩm', N'Bút, sổ, giấy in, kẹp ghim'),
(5, N'Mỹ phẩm & Chăm sóc da', N'Sữa rửa mặt, kem chống nắng'),
(6, N'Thực phẩm đóng gói', N'Mì gói, đồ hộp, gia vị, bánh kẹo'),
(7, N'Đồ chơi trẻ em', N'Lego, búp bê, xe mô hình'),
(8, N'Sách & Văn hóa phẩm', N'Sách giáo khoa, truyện tranh, tạp chí'),
(9, N'Thời trang cơ bản', N'Áo thun, tất, nón'),
(10, N'Thiết bị điện & Gia đình', N'Máy sấy, bàn ủi, quạt điện');


INSERT INTO Products (ProductID, CategoryID, ProductName, UnitPrice, UnitsInStock, Status) VALUES
(1, 1, N'iPhone 15 Pro Max 256GB', 30000000.00, 9, N'Còn hàng'), 
(2, 2, N'Nồi chiên không dầu Sunhouse 6L', 1500000.00, 0, N'Hết hàng'), 
(3, 3, N'Nước giặt OMO Matic 3.1kg', 185000.00, 95, N'Còn hàng'), 
(4, 4, N'Hộp 20 bút bi Thiên Long TL-027', 100000.00, 198, N'Còn hàng'),
(5, 5, N'Sữa rửa mặt Cerave 236ml', 350000.00, 0, N'Hết hàng'), 
(6, 6, N'Thùng mì Omachi Sườn Hầm', 240000.00, 86, N'Còn hàng'), 
(7, 7, N'Đồ chơi lắp ráp Lego City', 550000.00, 0, N'Hết hàng'), 
(8, 8, N'Truyện tranh Conan Tập 100', 25000.00, 86, N'Còn hàng'), 
(9, 9, N'Áo thun nam ngắn tay AIRism', 249000.00, 0, N'Hết hàng'), 
(10, 10, N'Máy sấy tóc Panasonic 1500W', 450000.00, 0, N'Hết hàng');


INSERT INTO Orders (OrderID, CustomerID, EmployeeID, OrderDate, TotalAmount, Status) VALUES
(1, 1, 3, '2026-03-01', 30000000.00, N'Đã thanh toán'), 
(2, 2, 4, '2026-03-02', 3000000.00, N'Đã thanh toán'),  
(3, 3, 8, '2026-03-03', 1032500.00, N'Chưa thanh toán'),
(4, 4, 3, '2026-03-04', 1050000.00, N'Đã thanh toán'),  
(5, 5, 4, '2026-03-05', 2400000.00, N'Đã thanh toán'),  
(6, 6, 8, '2026-03-06', 1100000.00, N'Đã thanh toán'),  
(7, 7, 3, '2026-03-07', 100000.00, N'Đã thanh toán'),   
(8, 8, 4, '2026-03-08', 250000.00, N'Đã thanh toán'), 
(9, 9, 8, '2026-03-09', 480000.00, N'Đã thanh toán'),   
(10, 10, 3, '2026-03-10', 1980000.00, N'Đã thanh toán');


INSERT INTO Order_Details (OrderID, ProductID, OrderedQuantity, Discount, SubTotal) VALUES
(1, 1, 1, 0.00, 30000000.00), 
(2, 2, 2, 0.00, 3000000.00),  
(3, 3, 5, 92500.00, 832500.00),
(3, 4, 2, 0.00, 200000.00),
(4, 5, 3, 0.00, 1050000.00),  
(5, 6, 10, 0.00, 2400000.00), 
(6, 7, 2, 0.00, 1100000.00), 
(7, 8, 4, 0.00, 100000.00),   
(8, 8, 10, 0.00, 250000.00), 
(9, 6, 2, 0.00, 480000.00),   
(10, 2, 1, 0.00, 1500000.00), 
(10, 6, 2, 0.00, 480000.00); 


INSERT INTO Bills (BillID, OrderID, PaymentAmount, PaymentDate, PaymentMethod) VALUES
(1, 1, 30000000.00, '2026-03-01', N'Chuyển khoản ngân hàng'),
(2, 2, 3000000.00, '2026-03-02', N'Ví điện tử'),
(3, 4, 1050000.00, '2026-03-04', N'Tiền mặt'),
(4, 5, 2400000.00, '2026-03-05', N'Chuyển khoản ngân hàng'),
(5, 6, 1100000.00, '2026-03-06', N'Tiền mặt'),
(6, 7, 100000.00, '2026-03-07', N'Tiền mặt'),
(7, 9, 480000.00, '2026-03-09', N'Ví điện tử'),          
(8, 10, 1980000.00, '2026-03-10', N'Chuyển khoản ngân hàng'),
(9, 8, 250000.00, '2026-03-08', N'Ví điện tử');


INSERT INTO Purchase_Orders (PurchaseOrderID, SupplierID, EmployeeID, PurchasedDate, ExpectedDate, ReceivedDate, TotalAmount, Status) VALUES
(1, 1, 7, '2026-01-05', '2026-01-10', '2026-01-10', 250000000.00, N'Đã nhận hàng'),
(2, 2, 7, '2026-01-15', '2026-01-20', '2026-01-20', 3000000.00, N'Đã nhận hàng'),  
(3, 3, 7, '2026-02-01', '2026-02-10', '2026-02-09', 14000000.00, N'Đã nhận hàng'),  
(4, 4, 7, '2026-02-10', '2026-02-15', '2026-02-15', 14000000.00, N'Đã nhận hàng'),  
(5, 5, 7, '2026-02-20', '2026-02-25', '2026-02-26', 750000.00, N'Đã nhận hàng'),   
(6, 6, 7, '2026-03-01', '2026-03-05', '2026-03-05', 19000000.00, N'Đã nhận hàng'),  
(7, 7, 7, '2026-02-25', '2026-03-01', '2026-03-02', 800000.00, N'Đã nhận hàng'),   
(8, 8, 7, '2026-02-28', '2026-03-03', '2026-03-03', 1800000.00, N'Đã nhận hàng'),   
(9, 9, 7, '2026-03-12', '2026-03-31', NULL, 750000.00, N'Chưa nhận hàng'),  
(10, 10, 7, '2026-03-14', '2026-03-30', NULL, 9000000.00, N'Chưa nhận hàng'); 

INSERT INTO Purchase_Details (PurchaseOrderID, ProductID, PurchasedQuantity, UnitCost, SubTotal) VALUES
(1, 1, 10, 25000000.00, 250000000.00), 
(2, 2, 3, 1000000.00, 3000000.00),        
(3, 3, 100, 140000.00, 14000000.00),   
(4, 4, 200, 70000.00, 14000000.00),    
(5, 5, 3, 250000.00, 750000.00),        
(6, 6, 100, 190000.00, 19000000.00),   
(7, 7, 2, 400000.00, 800000.00),        
(8, 8, 100, 18000.00, 1800000.00),      
(9, 9, 5, 150000.00, 750000.00),        
(10, 10, 30, 300000.00, 9000000.00);


INSERT INTO Promotions (PromotionID, PromotionName, PromotionForm, StartDate, EndDate, Status) VALUES
(1, N'Tết Nguyên Đán 2026', N'Giảm theo %', '2026-01-15', '2026-02-15', N'Đã kết thúc'),
(2, N'Lễ Tình Nhân', N'Giá trị', '2026-02-10', '2026-02-15', N'Đã kết thúc'),
(3, N'Quốc tế Phụ nữ 8/3', N'Giảm theo %', '2026-03-01', '2026-03-08', N'Đã kết thúc'),
(4, N'Sale Giữa Tháng 3', N'Giá trị', '2026-03-10', '2026-03-20', N'Đang diễn ra'),
(5, N'Mừng Lễ 30/4 - 1/5', N'Giảm theo %', '2026-04-20', '2026-05-05', N'Sắp diễn ra'),
(6, N'Mùa Hè Sôi Động', N'Giá trị', '2026-06-01', '2026-06-30', N'Sắp diễn ra'),
(7, N'Back to School', N'Giảm theo %', '2026-08-15', '2026-09-15', N'Sắp diễn ra'),
(8, N'Halloween Sale', N'Giá trị', '2026-10-25', '2026-10-31', N'Sắp diễn ra'),
(9, N'Black Friday', N'Giảm theo %', '2026-11-20', '2026-11-30', N'Sắp diễn ra'),
(10, N'Mừng Giáng Sinh', N'Giá trị', '2026-12-15', '2026-12-31', N'Sắp diễn ra');


INSERT INTO Promotion_Details (PromotionID, ProductID, ApplicableDate, DiscountRate, DiscountValue, DiscountedPrice) VALUES
(1, 1, '2026-01-20', 5.00, NULL, 28500000.00), 
(2, 2, '2026-02-12', NULL, 200000.00, 1300000.00),  
(3, 3, '2026-03-05', 10.00, NULL, 166500.00),   
(4, 4, '2026-03-15', NULL, 20000.00, 80000.00),     
(5, 5, '2026-04-25', 10.00, NULL, 315000.00),   
(6, 6, '2026-06-15', NULL, 40000.00, 200000.00),   
(7, 7, '2026-08-20', 20.00, NULL, 440000.00),  
(8, 8, '2026-10-30', NULL, 5000.00, 20000.00),     
(9, 9, '2026-11-25', 10.00, NULL, 224100.00),  
(10, 10, '2026-12-20', NULL, 50000.00, 400000.00);
