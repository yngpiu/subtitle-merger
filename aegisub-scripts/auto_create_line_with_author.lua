script_name = "Thêm Dòng Phụ Đề Là Tên Tác Giả"  -- Tên của macro
script_description = "Script này sẽ lấy tên tác giả từ dòng có tên tác giả, sau đó tạo dòng mới với thời gian giống dòng được lấy và dòng phụ đề đó là tên tác giả."  -- Mô tả chức năng của macro
script_author = "yngpiu"  -- Tác giả của macro
script_version = "1.0"  -- Phiên bản của macro

-- Hàm kiểm tra xem chuỗi str có bắt đầu bằng chuỗi start không
local function starts_with(str, start)
    return str:sub(1, #start) == start
end

-- Hàm chính để thêm dòng phụ đề mới với tên tác giả
function add_actor_line(subs, sel)
    local new_sel = {}  -- Tạo bảng chứa các chỉ số dòng mới
    for i, idx in ipairs(sel) do  -- Lặp qua các chỉ số dòng đã chọn
        local line = subs[idx]  -- Lấy dòng phụ đề hiện tại
        if line.actor ~= "" then  -- Nếu dòng có tên tác giả
            local new_line = line  -- Sao chép dòng hiện tại
            new_line.text = line.actor  -- Đặt text mới là tên tác giả
            new_line.actor = ""  -- Xóa tên tác giả trong dòng
            new_line.style = "ActorStyle"  -- Thiết lập style cho dòng mới
            subs.insert(idx + 1, new_line)  -- Chèn dòng mới vào sau dòng hiện tại
            table.insert(new_sel, idx + 1)  -- Thêm chỉ số dòng mới vào bảng new_sel
        end
    end
    aegisub.set_undo_point("Add Actor Name Line with Style")  -- Đánh dấu điểm hoàn tác
    return new_sel  -- Trả về bảng chỉ số dòng mới đã được thêm
end

aegisub.register_macro(script_name, script_description, add_actor_line)  -- Đăng ký macro để sử dụng trong Aegisub
