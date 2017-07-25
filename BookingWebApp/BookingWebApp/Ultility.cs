using System;
using System.Diagnostics;
using System.IO;
using System.Web.Mvc;

namespace BookingWebApp
{
    public class Ultility
    {
		public static void RunCMD(string cmd, string args)
		{
            ProcessStartInfo start = new ProcessStartInfo();
			start.FileName = "/usr/local/bin/pythonw";
			start.Arguments = string.Format("{0} {1}", cmd, args);
			start.UseShellExecute = false;
			start.RedirectStandardOutput = true;
			using (Process process = Process.Start(start))
			{
				using (StreamReader reader = process.StandardOutput)
				{
					string result = reader.ReadToEnd();
					Console.Write(result);
				}
			}
		}
        public static ContentResult GetJsonContent(object obj)
        {
			var jsonText = Newtonsoft.Json.JsonConvert.SerializeObject(obj);
			return new ContentResult { Content = jsonText, ContentType = "application/json", ContentEncoding = System.Text.Encoding.UTF8 };
		}
    }
}
