class PostsController < ApplicationController
  before_action :authenticate_user!

  def index
    @post = 'Hellow!'
    @username = session[:user]['name']
  end

end
