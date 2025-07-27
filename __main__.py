import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base64
import datetime
import json
import os

class LicenseManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Apple Music Downloader License Manager")
        self.root.geometry("600x500")
        
        # 创建许可证标签框架
        license_frame = ttk.LabelFrame(root, text="许可证信息", padding="10")
        license_frame.pack(fill="x", padx=10, pady=5)
        
        # 显示许可证信息
        self.license_text = tk.Text(license_frame, height=8, width=60)
        self.license_text.pack(fill="x", pady=5)
        
        # 加载许可证按钮
        load_button = ttk.Button(license_frame, text="加载许可证文件", command=self.load_license)
        load_button.pack(pady=5)
        
        # 验证许可证按钮
        validate_button = ttk.Button(license_frame, text="验证许可证", command=self.validate_license)
        validate_button.pack(pady=5)
        
        # 创建生成许可证标签框架
        generate_frame = ttk.LabelFrame(root, text="生成许可证", padding="10")
        generate_frame.pack(fill="x", padx=10, pady=5)
        
        # 许可证类型选择
        ttk.Label(generate_frame, text="许可证类型:").pack(anchor="w")
        self.license_type = tk.StringVar(value="temporary")
        temp_radio = ttk.Radiobutton(generate_frame, text="临时许可证", variable=self.license_type, 
                                     value="temporary", command=self.toggle_lifetime_fields)
        perm_radio = ttk.Radiobutton(generate_frame, text="永久许可证", variable=self.license_type, 
                                     value="permanent", command=self.toggle_lifetime_fields)
        temp_radio.pack(anchor="w")
        perm_radio.pack(anchor="w")
        
        # 有效期设置
        self.duration_frame = ttk.Frame(generate_frame)
        self.duration_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.duration_frame, text="天数:").grid(row=0, column=0, sticky="w")
        self.days_var = tk.StringVar(value="7")
        days_entry = ttk.Entry(self.duration_frame, textvariable=self.days_var, width=10)
        days_entry.grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(self.duration_frame, text="小时数:").grid(row=0, column=2, sticky="w")
        self.hours_var = tk.StringVar(value="0")
        hours_entry = ttk.Entry(self.duration_frame, textvariable=self.hours_var, width=10)
        hours_entry.grid(row=0, column=3, padx=(5, 0))
        
        # 输出文件名
        ttk.Label(generate_frame, text="输出文件名:").pack(anchor="w", pady=(10, 0))
        self.output_var = tk.StringVar(value="license.key")
        output_entry = ttk.Entry(generate_frame, textvariable=self.output_var, width=40)
        output_entry.pack(fill="x", pady=5)
        
        # 生成按钮
        generate_button = ttk.Button(generate_frame, text="生成许可证", command=self.generate_license)
        generate_button.pack(pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
        
        # 初始化界面
        self.toggle_lifetime_fields()
        
    def toggle_lifetime_fields(self):
        """根据许可证类型切换有效期输入框状态"""
        if self.license_type.get() == "permanent":
            # 禁用临时许可证的输入框
            for child in self.duration_frame.winfo_children():
                if isinstance(child, ttk.Entry):
                    child.configure(state="disabled")
        else:
            # 启用临时许可证的输入框
            for child in self.duration_frame.winfo_children():
                if isinstance(child, ttk.Entry):
                    child.configure(state="normal")
    
    def generate_license_key(self, days=7, hours=0, output_file="license.key", lifetime=False):
        """
        生成许可证密钥
        """
        # 生成密钥
        current_time = datetime.datetime.now()
        key_data = {
            "created_at": current_time.isoformat(),
        }
        
        if lifetime:
            key_data["lifetime"] = True
            expiry_time = None
        else:
            expiry_time = current_time + datetime.timedelta(days=days, hours=hours)
            key_data["expires_at"] = expiry_time.isoformat()
        
        # 编码密钥
        key_json = json.dumps(key_data)
        key = base64.b64encode(key_json.encode()).decode()
        
        # 保存到文件
        with open(output_file, "w") as f:
            f.write(key)
        
        return key, current_time, expiry_time
    
    def generate_license(self):
        """生成许可证"""
        try:
            output_file = self.output_var.get()
            if not output_file:
                output_file = "license.key"
            
            if self.license_type.get() == "permanent":
                key, created_time, expiry_time = self.generate_license_key(0, 0, output_file, True)
                message = f"永久许可证已生成\n创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                days = int(self.days_var.get()) if self.days_var.get() else 7
                hours = int(self.hours_var.get()) if self.hours_var.get() else 0
                
                if days < 0 or hours < 0:
                    messagebox.showerror("错误", "有效期不能为负数")
                    return
                    
                key, created_time, expiry_time = self.generate_license_key(days, hours, output_file, False)
                message = f"临时许可证已生成\n创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"过期时间: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"有效期: {days}天 {hours}小时"
            
            # 显示许可证信息
            self.license_text.delete(1.0, tk.END)
            self.license_text.insert(tk.END, f"许可证文件: {os.path.abspath(output_file)}\n\n")
            self.license_text.insert(tk.END, key)
            
            messagebox.showinfo("成功", message)
            self.status_var.set("许可证生成成功")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
        except Exception as e:
            messagebox.showerror("错误", f"生成许可证时出错: {str(e)}")
    
    def load_license(self):
        """加载许可证文件"""
        file_path = filedialog.askopenfilename(
            title="选择许可证文件",
            filetypes=[("License Files", "*.key"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r") as f:
                    key = f.read().strip()
                
                # 显示许可证内容
                self.license_text.delete(1.0, tk.END)
                self.license_text.insert(tk.END, f"许可证文件: {os.path.abspath(file_path)}\n\n")
                self.license_text.insert(tk.END, key)
                
                self.status_var.set(f"已加载许可证文件: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"加载许可证文件时出错: {str(e)}")
    
    def validate_license(self):
        """验证许可证"""
        try:
            # 获取文本框中的许可证内容
            content = self.license_text.get(1.0, tk.END).strip()
            
            # 提取实际的许可证字符串（去掉文件路径等信息）
            lines = content.split('\n')
            key = None
            for line in lines:
                if not line.startswith("许可证文件:"):
                    key = line
                    break
            
            if not key:
                messagebox.showwarning("警告", "未找到有效的许可证")
                return
            
            # 解码许可证
            key_json = base64.b64decode(key.encode()).decode()
            key_data = json.loads(key_json)
            
            # 检查许可证信息
            created_at = datetime.datetime.fromisoformat(key_data["created_at"])
            
            if key_data.get("lifetime", False):
                # 永久许可证
                message = f"许可证有效\n\n类型: 永久许可证\n创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                # 临时许可证
                expires_at = datetime.datetime.fromisoformat(key_data["expires_at"])
                current_time = datetime.datetime.now()
                
                if current_time > expires_at:
                    # 许可证已过期
                    message = f"许可证已过期\n\n类型: 临时许可证\n创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"过期时长: {(current_time - expires_at).days}天"
                else:
                    # 许可证有效
                    remaining = expires_at - current_time
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    message = f"许可证有效\n\n类型: 临时许可证\n创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"剩余时间: {days}天 {hours}小时"
            
            messagebox.showinfo("验证结果", message)
            self.status_var.set("许可证验证完成")
            
        except Exception as e:
            messagebox.showerror("验证失败", f"许可证验证失败: {str(e)}")

def main():
    root = tk.Tk()
    app = LicenseManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()