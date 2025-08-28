"""
版本信息模块
包含程序的作者、版本、创建时间等信息
"""

__version__ = "V1.0"
__author__ = "正明"
__create_date__ = "20250822"
__license__ = "该程序完全免费，不进行任何盈利"

class VersionInfo:
    """版本信息类"""
    
    VERSION = __version__
    AUTHOR = __author__
    CREATE_DATE = __create_date__
    LICENSE = __license__
    
    @classmethod
    def get_version_string(cls) -> str:
        """获取版本信息字符串"""
        return f"Windows语音输入工具 {cls.VERSION}"
    
    @classmethod
    def get_author_info(cls) -> str:
        """获取作者信息"""
        return f"作者: {cls.AUTHOR}"
    
    @classmethod
    def get_create_date(cls) -> str:
        """获取创建日期"""
        return f"创建时间: {cls.CREATE_DATE}"
    
    @classmethod
    def get_license_info(cls) -> str:
        """获取许可证信息"""
        return cls.LICENSE
    
    @classmethod
    def get_full_info(cls) -> str:
        """获取完整信息"""
        return f"""{cls.get_version_string()}

{cls.get_author_info()}
{cls.get_create_date()}

{cls.get_license_info()}"""
    
    @classmethod
    def print_startup_info(cls):
        """打印启动信息"""
        print("=" * 50)
        print(cls.get_version_string())
        print(cls.get_author_info())
        print(cls.get_create_date())
        print(cls.get_license_info())
        print("=" * 50)