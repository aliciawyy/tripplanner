using System;
namespace BookingWebApp.Models
{
    public class Activity
    {
        public Activity()
        {
        }
        public string Longitude { get; set; }
        public string Latitude { get; set; }
        public string ImageUrl { get; set; }
        public string Type { get; set; }
        public double Rating { get; set; }
        public string Name { get; set; }
        public string Id { get; set; }
        public int Day { get; set; }
    }
}
