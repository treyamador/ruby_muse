class User < ApplicationRecord
  require 'uri'

  # Include default devise modules. Others available are:
  # :confirmable, :lockable, :timeoutable, :trackable and :omniauthable
  devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :validatable

  has_many :postings, dependent: :destroy

  validates :first_name, presence: true, length: { maximum: 255 }
  validates :middle_name, length: { maximum: 255 }
  validates :last_name, presence: true, length: { maximum: 255 }
  validates :email, presence: true, uniqueness: true,
                    format: { with: Devise.email_regexp }

  # TODO: add additional password validation?
  # def password_validate() end
end
