using System;
namespace BookingWebApp.Models
{
    public class Day
    {
        public Day()
        {
        }
        public int NumberOfActivity { get; set; }
        public System.Collections.Generic.List<Activity> Activities { get; set; }
    }
}
