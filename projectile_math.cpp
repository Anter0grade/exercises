#include <iostream>
#include <cmath>

const double g = 9.81;
/*
(v_0 * sin(theta) + sqrt( (v_0*sin(theta))^2 + 2gh)) / g
*/


double time_to_ground(double h, double v_0, double theta){
    if (h < 0){return -1;}
    if (v_0 < 0){return -1;}

    // conv to radians, sin() expects radians
    double theta_radians = theta * M_PI / 180.0;
    // precompute sin(theta)
    // note: we only precompute here because it appears twice 
    double sin_theta = sin(theta_radians);

    double t = (v_0 * sin_theta 
    + sqrt(pow(v_0 * sin_theta, 2) + 2 * g * h)) / g;

    return t;
}

/*
h + ((v_0*(sin(theta))^2)/2
*/

double max_height(double h, double v_0, double theta){
    if (h < 0){return -1;}
    if (v_0 < 0){return -1;}

    double theta_radians = theta * M_PI / 180.0;
    
    double v_y = v_0 * sin(theta_radians);
    double max_h = h + (v_y * v_y) / (2 * g);

    return max_h;
}

/*
v_0 * cos(theta) * t_to_ground
*/

// how far it travels
double horizontal_range(double h, double v_0, double theta){
    if (v_0 < 0){return -1;}

    // conv to radians, sin() expects radians
    double theta_radians = theta * M_PI / 180.0;
    
    double v_x = v_0 * cos(theta_radians);
    double range = v_x * time_to_ground(h, v_0, theta);

    return range;
}

/*
v_xf = v_0 * cos(theta)
v_yf = (v_0 * sin(theta)) - g * t_to_ground
v_f = sqrt( v_xf^2 + v_yf^2 )
*/

double final_velocity(double h, double v_0, double theta){
    if (h < 0){return -1;}
    if (v_0 < 0){return -1;}

    double theta_radians = theta * M_PI / 180.0;

    double v_xf = v_0 * cos(theta_radians);
    double v_yf = (v_0 * sin(theta)) - g * time_to_ground(h, v_0, theta);
    
    double v_f = sqrt((v_xf*v_xf) + (v_yf*v_yf));

    return v_f;
}

struct coordinates {
    double x;
    double y;
    bool valid; // for error handling
};

/*
horizontal = (v_0 * cos(theta)) * t
vertical = h + (v_0 * sin(theta)) * t - ((g/2)*t^2)
*/

coordinates position_at_time(double h, double v_0, double theta, double t){
    if (h < 0 || v_0 < 0 || t < 0) {
        return {0, 0, false};
    }

    double theta_radians = theta * M_PI / 180.0;

    double x = v_0 * cos(theta_radians) * t;
    double y = h + v_0 * sin(theta_radians) * t 
    - 0.5 * 9.81 * t * t;

    return {x, y, true};
}

int main(){
    double h = 10;
    double v_0 = 40;
    double theta = 45;

    double t = 2;

    coordinates position = position_at_time(h, v_0, theta, t);
    if (!position.valid) {
        std::cout << "invalid input" << std::endl;
    } else {
        std::cout <<
        "time to ground: " << time_to_ground(h, v_0, theta)
        <<
        "\nmax height: " << max_height(h, v_0, theta)
        <<
        "\nhorizontal range: " << horizontal_range(h, v_0, theta)
        <<
        "\nfinal velocity: " << final_velocity(h, v_0, theta)
        <<
        "\nposition at " << t << "s: " << "\n\tx: " << position.x 
        <<
        "\n\ty: " << position.y << std::endl;

    }
}