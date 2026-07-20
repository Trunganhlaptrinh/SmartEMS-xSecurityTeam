// view/main.js
// util phía frontend: gọi API backend, hiển thị toast, helper dùng chung
// tương tự Validation.java — nhưng chạy ở trình duyệt

// =============================
// CẤU HÌNH API BASE URL
// =============================
// Khi chạy local: "http://localhost:5000/api"
// Khi deploy lên Render: đổi thành URL của Render
// cùng server nên dùng đường dẫn tương đối, không cần ghi full URL
// khi deploy lên Render thì tự động đúng luôn, không cần sửa
const BASE_URL = "/api";

// =============================
// API HELPER
// tương tự các hàm static trong Validation.java
// =============================
const API = {
  // gọi GET request
  async get(path) {
    try {
      const res = await fetch(BASE_URL + path, {
        credentials: "include"
      });
      return await res.json();
    } catch (err) {
      console.error("GET error:", err);
      return { success: false, message: "Lỗi kết nối server" };
    }
  },

  // gọi POST request với body JSON
  async post(path, body) {
    try {
      const res = await fetch(BASE_URL + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body)
      });
      return await res.json();
    } catch (err) {
      console.error("POST error:", err);
      return { success: false, message: "Lỗi kết nối server" };
    }
  },

  // gọi PUT request (cập nhật)
  async put(path, body) {
    try {
      const res = await fetch(BASE_URL + path, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body)
      });
      return await res.json();
    } catch (err) {
      console.error("PUT error:", err);
      return { success: false, message: "Lỗi kết nối server" };
    }
  },

  // gọi DELETE request (hỗ trợ gửi kèm body JSON, ví dụ { api_key: ... })
  async delete(path, body) {
    try {
      const options = {
        method: "DELETE",
        credentials: "include"
      };
      if (body !== undefined) {
        options.headers = { "Content-Type": "application/json" };
        options.body = JSON.stringify(body);
      }
      const res = await fetch(BASE_URL + path, options);
      return await res.json();
    } catch (err) {
      console.error("DELETE error:", err);
      return { success: false, message: "Lỗi kết nối server" };
    }
  }
};

// =============================
// TOAST NOTIFICATION
// hiển thị thông báo góc dưới phải
// =============================
let toastTimer = null;

function showToast(message, type = "default") {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.textContent = message;
  toast.className = "show " + type;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.className = "";
  }, 2800);
}

// =============================
// MODAL HELPER
// =============================
function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

// =============================
// FORMAT TIỀN VIỆT NAM
// =============================
function formatMoney(amount) {
  return Number(amount).toLocaleString("vi-VN") + " ₫";
}

// =============================
// FORMAT NGÀY
// =============================
function formatDate(dateStr) {
  if (!dateStr) return "—";
  const [y, m, d] = dateStr.split("-");
  return `${d}/${m}/${y}`;
}

// =============================
// BADGE HTML HELPER
// =============================
function badgeStatus(status) {
  const map = {
    present: ["badge-green", "Có mặt"],
    absent: ["badge-red", "Vắng"],
    late: ["badge-yellow", "Đi muộn"],
    approved: ["badge-green", "Đã duyệt"],
    rejected: ["badge-red", "Từ chối"],
    pending: ["badge-yellow", "Chờ duyệt"],
  };

  const [cls, label] = map[status] || ["badge-gray", status];
  return `<span class="badge ${cls}">${label}</span>`;
}

// =============================
// KIỂM TRA ĐĂNG NHẬP
// =============================
async function requireLogin() {
  const res = await API.get("/auth/me");

  if (!res.success) {
    window.location.href = "index.html";
    return null;
  }

  return res;
}

// =============================
// LẤY AVATAR CỦA NGƯỜI DÙNG
// =============================
let cachedAvatar = null;
let avatarLoading = false;

async function getUserAvatar() {
  // Nếu đã có trong cache thì trả về luôn
  if (cachedAvatar !== null) {
    return cachedAvatar;
  }

  // Tránh gọi API nhiều lần cùng lúc
  if (avatarLoading) {
    // Chờ cho đến khi load xong
    return new Promise((resolve) => {
      const checkCache = setInterval(() => {
        if (!avatarLoading) {
          clearInterval(checkCache);
          resolve(cachedAvatar);
        }
      }, 100);
    });
  }

  avatarLoading = true;
  try {
    const res = await API.get("/auth/profile");
    if (res.success && res.data && res.data.avatar) {
      cachedAvatar = res.data.avatar;
    } else {
      cachedAvatar = null;
    }
  } catch (err) {
    console.error("Lỗi lấy avatar:", err);
    cachedAvatar = null;
  } finally {
    avatarLoading = false;
  }

  return cachedAvatar;
}

// =============================
// RENDER SIDEBAR
// =============================
function renderSidebar(currentPage, user) {
  const isAdmin = user.role === "admin";

  // Links dành cho Admin (chỉ giữ Quản lí nhân viên)
  const adminLinks = isAdmin ? `
    <a class="nav-item ${currentPage === 'employees' ? 'active' : ''}" href="employees.html">
      <img src="image/logo_quan_li_nhan_vien.png" style="height:18px;width:18px;object-fit:contain;" />
      HR
    </a>
  ` : "";

  document.getElementById("sidebar").innerHTML = `
    <div class="sidebar-logo">
      <img src="image/logo_E.png" style="height:22px;vertical-align:middle;margin-right:6px;" />
      Smart<span>EMS</span>
    </div>

    <a class="nav-item ${currentPage === 'dashboard' ? 'active' : ''}" href="dashboard.html">
      <img src="image/logo_ngoi_nha.png" style="height:18px;width:18px;object-fit:contain;" />
      Trang chủ
    </a>

    <a class="nav-item ${currentPage === 'attendance' ? 'active' : ''}" href="attendance.html">
      <img src="image/logo_diem_danh.png" style="height:18px;width:18px;object-fit:contain;" />
      Điểm danh
    </a>

    <a class="nav-item ${currentPage === 'leave' ? 'active' : ''}" href="leave.html">
      <img src="image/logo_nghi_phep.png" style="height:18px;width:18px;object-fit:contain;" />
      Nghỉ phép
    </a>

    <a class="nav-item ${currentPage === 'salary' ? 'active' : ''}" href="salary.html">
      <img src="image/logo_luong.png" style="height:18px;width:18px;object-fit:contain;" />
      Lương thưởng
    </a>

    <a class="nav-item ${currentPage === 'shop' ? 'active' : ''}" href="shop.html">
      <img src="image/logo_shop.png" style="height:18px;width:18px;object-fit:contain;" />
      SHOP NẠP VIP
    </a>

    <a class="nav-item ${currentPage === 'notifications' ? 'active' : ''}" href="notifications.html">
      <img src="image/logo_thong_bao.png" style="height:18px;width:18px;object-fit:contain;" />
      Thông báo
    </a>

    <a class="nav-item ${currentPage === 'projects' ? 'active' : ''}" href="projects.html">
      <img src="image/logo_project.png" style="height:18px;width:18px;object-fit:contain;" />
      Dự án
    </a>

    <a class="nav-item ${currentPage === 'contracts' ? 'active' : ''}" href="contracts.html">
      <span>🔒</span>
      Hợp đồng
    </a>

    <!-- Task Management - GIỮ NGUYÊN -->
    <a class="nav-item ${currentPage === 'tasks' ? 'active' : ''}" href="tasks.html">
      <span>📋</span>
      Quản lý Task
    </a>

    <!-- ChatEMS - DÙNG logo_chatems.png -->
    <a class="nav-item ${currentPage === 'chatems' ? 'active' : ''}" href="chatems.html">
      <img src="image/logo_chatems.png" style="height:18px;width:18px;object-fit:contain;" />
      ChatEMS
    </a>

    ${adminLinks}

    <div class="sidebar-bottom">
      <a class="nav-item ${currentPage === 'profile' ? 'active' : ''}" href="profile.html" style="margin-bottom:4px;">
        <span class="profile-avatar-container"><span class="icon">👤</span></span>
        Hồ sơ
      </a>
      <button class="nav-item" onclick="doLogout()">
        <img src="image/logo_dang_xuat.png" style="height:18px;width:18px;object-fit:contain;" />
        Đăng xuất
      </button>
    </div>
  `;

  getUserAvatar().then(avatar => {
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;

    const profileContainer = sidebar.querySelector('.profile-avatar-container');
    if (profileContainer) {
      if (avatar) {
        profileContainer.innerHTML = `<img src="${avatar}" style="width:20px;height:20px;border-radius:50%;object-fit:cover;border:1.5px solid var(--border);" />`;
      } else {
        profileContainer.innerHTML = `<span class="icon">👤</span>`;
      }
    }
  });
}

// =============================
// XỬ LÝ ĐĂNG XUẤT
// =============================
async function doLogout() {
  await API.post("/auth/logout", {});
  // Reset cache avatar khi đăng xuất
  cachedAvatar = null;
  window.location.href = "index.html";
}

// =============================
// HÀM LÀM MỚI AVATAR TRÊN SIDEBAR (gọi sau khi upload avatar)
// =============================
function refreshSidebarAvatar() {
  // Reset cache để load lại avatar mới
  cachedAvatar = null;
  // Gọi lại renderSidebar với page hiện tại
  const currentPage = window.location.pathname.split('/').pop().replace('.html', '') || 'dashboard';
  // Lấy thông tin user từ session
  API.get("/auth/me").then(res => {
    if (res.success) {
      renderSidebar(currentPage, res);
    }
  });
}