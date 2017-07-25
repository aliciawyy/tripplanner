using System;
using System.Web.Mvc;

namespace BookingWebApp
{
	public class AllowCrossSiteJsonAttribute : ActionFilterAttribute
	{
		public override void OnActionExecuting(System.Web.Mvc.ActionExecutingContext filterContext)
		{
			filterContext.RequestContext.HttpContext.Response.AddHeader("Access-Control-Allow-Origin", "*");
            filterContext.RequestContext.HttpContext.Response.AddHeader("Access-Control-Allow-Methods","*");
			base.OnActionExecuting(filterContext);
		}
	}
}
