import base64
import datetime
import json
import os
import argparse

def generate_key(days=7, hours=0, output_file="license.key", lifetime=False):
    """
    生成具有指定有效期的密钥
    :param days: 有效期天数
    :param hours: 有效期小时数
    :param output_file: 输出文件名
    :param lifetime: 是否为永久许可证
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
    
    print(f"密钥已生成：{key}")
    print(f"密钥文件已保存到：{os.path.abspath(output_file)}")
    print(f"生成时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if lifetime:
        print("许可证类型：永久有效")
    else:
        print(f"有效期至：{expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总有效期：{days}天{hours}小时")

def interactive_mode():
    """交互式生成许可证"""
    print("Apple Music Downloader 许可证生成器 - 交互模式")
    print("-" * 50)
    
    while True:
        print("\n请选择许可证类型：")
        print("1. 临时许可证")
        print("2. 永久许可证")
        print("3. 退出")
        
        choice = input("\n请输入选项 (1-3): ").strip()
        
        if choice == "3":
            return
        elif choice not in ["1", "2"]:
            print("无效的选项，请重试")
            continue
            
        output_file = input("\n请输入输出文件名 (直接回车使用默认值 'license.key'): ").strip()
        if not output_file:
            output_file = "license.key"
            
        if choice == "1":
            while True:
                try:
                    days = int(input("\n请输入有效期天数: ").strip())
                    hours = int(input("请输入额外的小时数: ").strip())
                    if days < 0 or hours < 0:
                        print("错误：有效期不能为负数")
                        continue
                    generate_key(days, hours, output_file, False)
                    break
                except ValueError:
                    print("错误：请输入有效的数字")
        else:  # choice == "2"
            generate_key(0, 0, output_file, True)
            
        print("\n是否继续生成其他许可证？")
        if input("输入 'y' 继续，其他键退出: ").lower() != 'y':
            break

def main():
    parser = argparse.ArgumentParser(
        description="Apple Music Downloader 许可证密钥生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  1. 交互式生成许可证:
     python keygen.py

  2. 生成30天有效期的许可证:
     python keygen.py -d 30

  3. 生成永久有效的许可证:
     python keygen.py -l

  4. 生成15天12小时有效期的许可证:
     python keygen.py -d 15 -H 12

  5. 指定输出文件名:
     python keygen.py -d 30 -o custom_license.key
""")
    
    group = parser.add_argument_group("许可证选项")
    group.add_argument("-d", "--days", type=int,
                      help="有效期天数（默认：7天）")
    group.add_argument("-H", "--hours", type=int,
                      help="额外的有效期小时数（默认：0小时）")
    group.add_argument("-l", "--lifetime", action="store_true",
                      help="生成永久有效的许可证（此选项将忽略 -d 和 -H 参数）")
    
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument("-o", "--output", type=str,
                      help="输出文件名（默认：license.key）")
    
    args = parser.parse_args()
    
    # 如果没有提供任何参数，进入交互模式
    if not any([args.days is not None, args.hours is not None, 
                args.lifetime, args.output]):
        interactive_mode()
        return
        
    # 设置默认值
    days = 7 if args.days is None else args.days
    hours = 0 if args.hours is None else args.hours
    output = "license.key" if args.output is None else args.output
    
    if not args.lifetime and (days < 0 or hours < 0):
        print("错误：有效期不能为负数")
        return
    
    generate_key(days, hours, output, args.lifetime)

if __name__ == "__main__":
    main()
