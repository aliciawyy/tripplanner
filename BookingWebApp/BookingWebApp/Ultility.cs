using System;
using System.Diagnostics;
using System.IO;

namespace BookingWebApp
{
    public class Ultility
    {
		public static void run_cmd(string cmd, string args)
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
    }
}
