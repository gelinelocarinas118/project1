<?php

namespace App\Http\Controllers\file;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class CallbackController extends Controller
{
    public function reconstructionDone(){
     
        // update db status that the model is done for specific timestamp
        // the react expo will periodically checks if the model is ready from its status
        

    }
}
